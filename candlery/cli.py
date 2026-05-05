"""Command line interface for Candlery."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

from candlery.backtest.costs import transaction_cost_model_from_mapping
from candlery.backtest.runner import BacktestConfig, BacktestRunner
from candlery.data.calendar import TradingCalendar
from candlery.data.provider import BhavcopyDataProvider
from candlery.journal.run_journal import RunJournal
from candlery.risk.engine import RiskEngine
from candlery.strategy.sma_crossover import SMACrossover
from candlery.strategy.volatility_breakout import VolatilityBreakout

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("candlery.cli")


def _load_yaml(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _build_runner_from_args(
    args: argparse.Namespace,
    *,
    with_journal: bool = False,
) -> tuple[BacktestRunner, Path, set[str], date, date]:
    """Build a BacktestRunner and shared context from CLI args."""
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    logger.info(f"Loading backtest config from {config_path}")
    config_data = _load_yaml(config_path)
    
    bt_params = config_data.get("backtest", {})
    strategy_params = config_data.get("strategy_params", {})
    
    # 1. Parse dates
    start_date = datetime.strptime(bt_params["start_date"], "%Y-%m-%d").date()
    end_date = datetime.strptime(bt_params["end_date"], "%Y-%m-%d").date()
    
    # 2. Load universe
    universe_name = bt_params["universe"]
    universe_path = config_path.parent / "universes" / f"{universe_name}.yaml"
    if not universe_path.exists():
        logger.error(f"Universe file not found: {universe_path}")
        sys.exit(1)
        
    universe_data = _load_yaml(universe_path)
    universe = set(universe_data.get("symbols", []))
    logger.info(f"Loaded universe {universe_name} with {len(universe)} symbols")
    
    # 3. Load risk profile
    risk_profile_name = bt_params["risk_profile"]
    risk_path = config_path.parent / f"{risk_profile_name}_defaults.yaml"
    if not risk_path.exists():
        logger.error(f"Risk profile not found: {risk_path}")
        sys.exit(1)

    risk_file_data = _load_yaml(risk_path)
    risk_data = risk_file_data.get(risk_profile_name)
    if not isinstance(risk_data, dict):
        logger.error(
            "Risk profile key '%s' missing in %s",
            risk_profile_name,
            risk_path,
        )
        sys.exit(1)
    
    # 4. Initialize components
    calendar = TradingCalendar(exchange=bt_params["exchange"])
    
    logger.info(f"Loading data from {args.data_dir}...")
    provider = BhavcopyDataProvider(args.data_dir, start_date, end_date, calendar)
    
    strategy_name = bt_params.get("strategy", "sma_crossover")
    if strategy_name == "sma_crossover":
        strategy = SMACrossover(
            fast_period=strategy_params.get("fast_period", 10),
            slow_period=strategy_params.get("slow_period", 30),
            trend_filter_period=strategy_params.get("trend_filter_period"),
            min_trend_strength_pct=strategy_params.get("min_trend_strength_pct", 0.0),
            atr_filter_period=strategy_params.get("atr_filter_period"),
            min_atr_pct=strategy_params.get("min_atr_pct", 0.0),
            cooldown_bars=strategy_params.get("cooldown_bars", 0),
            trailing_stop_lookback=strategy_params.get("trailing_stop_lookback"),
            trailing_stop_atr_period=strategy_params.get("trailing_stop_atr_period"),
            trailing_stop_atr_mult=strategy_params.get("trailing_stop_atr_mult", 0.0),
        )
    elif strategy_name == "volatility_breakout":
        strategy = VolatilityBreakout(
            breakout_lookback=strategy_params.get("breakout_lookback", 20),
            atr_period=strategy_params.get("atr_period", 14),
            max_atr_pct=strategy_params.get("max_atr_pct", 3.0),
            volume_lookback=strategy_params.get("volume_lookback", 20),
            min_volume_ratio=strategy_params.get("min_volume_ratio", 1.2),
        )
    else:
        logger.error("Unsupported strategy: %s", strategy_name)
        sys.exit(1)
                            
    risk_engine = RiskEngine(risk_data)
    
    config = BacktestConfig(
        start_date=start_date,
        end_date=end_date,
        initial_capital=bt_params.get("initial_capital", 100000.0),
        universe=universe,
        cost_model=transaction_cost_model_from_mapping(bt_params.get("costs")),
    )

    runner_kwargs: dict[str, object] = {}
    if with_journal:
        run_id = getattr(args, "run_id", None) or config_path.stem
        journal_path = getattr(args, "journal", None)
        if not journal_path:
            journal_path = f"reports/paper_{run_id}.jsonl"
        runner_kwargs = {
            "journal": RunJournal(journal_path),
            "run_id": run_id,
            "resume_from_journal": bool(getattr(args, "resume", False)),
        }

    runner = BacktestRunner(
        config=config,
        calendar=calendar,
        importer=provider,
        strategy=strategy,
        risk_engine=risk_engine,
        **runner_kwargs,
    )
    return runner, config_path, universe, start_date, end_date


def _render_and_write_outputs(
    *,
    args: argparse.Namespace,
    result,
    config_path: Path,
    start_date: date,
    end_date: date,
    universe: set[str],
) -> None:
    # Report
    print("\n" + "=" * 50)
    print("BACKTEST RESULTS")
    print("=" * 50)
    print(f"Total Return:   {result.metrics.total_return_pct:.2f}%")
    print(f"Max Drawdown:   {result.metrics.max_drawdown_pct:.2f}%")
    print(f"Win Rate:       {result.metrics.win_rate_pct:.2f}%")
    print(f"Sharpe Ratio:   {result.metrics.sharpe_ratio:.2f}")
    print(f"Total Trades:   {result.metrics.total_trades}")
    if result.daily_equity_curve:
        print(f"Final Equity:   {result.daily_equity_curve[-1]:.2f}")
    else:
        print("Final Equity:   n/a")
    print("=" * 50)

    if result.trades:
        print("\nLast 5 Trades:")
        for t in result.trades[-5:]:
            print(
                f"  {t.date} | {t.signal.name:4s} | {t.symbol:10s} | QTY: {t.quantity:4d} | PNL: {t.realized_pnl:.2f}"
            )

    html_path = getattr(args, "html", None)
    if html_path:
        from candlery.reporting.html import write_html_report

        write_html_report(
            html_path,
            result,
            title=config_path.stem,
            start_date=start_date,
            end_date=end_date,
            universe_size=len(universe),
        )
        logger.info("Wrote HTML report to %s", html_path)

    csv_prefix = getattr(args, "csv", None)
    if csv_prefix:
        from candlery.reporting.csv import write_csv_bundle

        out = write_csv_bundle(
            csv_prefix,
            result,
            title=config_path.stem,
            start_date=start_date,
            end_date=end_date,
            universe_size=len(universe),
        )
        logger.info(
            "Wrote CSV report bundle: %s, %s, %s",
            out["summary"],
            out["trades"],
            out["equity"],
        )


def run_backtest(args: argparse.Namespace) -> None:
    """Run a backtest from a configuration file."""
    runner, config_path, universe, start_date, end_date = _build_runner_from_args(
        args, with_journal=False
    )
    result = runner.run()
    _render_and_write_outputs(
        args=args,
        result=result,
        config_path=config_path,
        start_date=start_date,
        end_date=end_date,
        universe=universe,
    )


def run_paper(args: argparse.Namespace) -> None:
    """Run forward-style paper simulation with persistent RunJournal."""
    runner, config_path, universe, start_date, end_date = _build_runner_from_args(
        args, with_journal=True
    )
    result = runner.run()
    _render_and_write_outputs(
        args=args,
        result=result,
        config_path=config_path,
        start_date=start_date,
        end_date=end_date,
        universe=universe,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Candlery Algorithmic Trading Platform")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Backtest subcommand
    bt_parser = subparsers.add_parser("backtest", help="Run a backtest simulation")
    bt_parser.add_argument("--config", required=True, help="Path to backtest YAML config")
    bt_parser.add_argument("--data-dir", default="data", help="Directory containing Bhavcopy CSVs")
    bt_parser.add_argument(
        "--html",
        default=None,
        metavar="PATH",
        help="Write static HTML tear sheet to this path after the run",
    )
    bt_parser.add_argument(
        "--csv",
        default=None,
        metavar="PATH_PREFIX",
        help="Write CSV bundle (<prefix>_summary/trades/equity.csv)",
    )

    # Paper subcommand (Phase 3D)
    paper_parser = subparsers.add_parser(
        "paper", help="Run deterministic paper simulation with resume support"
    )
    paper_parser.add_argument("--config", required=True, help="Path to backtest YAML config")
    paper_parser.add_argument("--data-dir", default="data", help="Directory containing Bhavcopy CSVs")
    paper_parser.add_argument(
        "--journal",
        default=None,
        metavar="PATH",
        help="Path to run journal JSONL (default: reports/paper_<run_id>.jsonl)",
    )
    paper_parser.add_argument(
        "--run-id",
        default=None,
        metavar="ID",
        help="Logical run identifier used inside the journal",
    )
    paper_parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from the latest completed day in the journal",
    )
    paper_parser.add_argument(
        "--html",
        default=None,
        metavar="PATH",
        help="Write static HTML tear sheet to this path after the run",
    )
    paper_parser.add_argument(
        "--csv",
        default=None,
        metavar="PATH_PREFIX",
        help="Write CSV bundle (<prefix>_summary/trades/equity.csv)",
    )
    
    args = parser.parse_args()
    
    if args.command == "backtest":
        run_backtest(args)
    elif args.command == "paper":
        run_paper(args)

if __name__ == "__main__":
    main()
