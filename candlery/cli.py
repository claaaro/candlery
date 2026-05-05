"""Command line interface for Candlery."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

from candlery.backtest.costs import transaction_cost_model_from_mapping
from candlery.backtest.runner import BacktestConfig, BacktestRunner
from candlery.data.calendar import TradingCalendar
from candlery.data.provider import BhavcopyDataProvider
from candlery.risk.engine import RiskEngine
from candlery.strategy.sma_crossover import SMACrossover

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("candlery.cli")


def _load_yaml(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def run_backtest(args: argparse.Namespace) -> None:
    """Run a backtest from a configuration file."""
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
    
    strategy = SMACrossover(fast_period=strategy_params.get("fast_period", 10),
                            slow_period=strategy_params.get("slow_period", 30))
                            
    risk_engine = RiskEngine(risk_data)
    
    config = BacktestConfig(
        start_date=start_date,
        end_date=end_date,
        initial_capital=bt_params.get("initial_capital", 100000.0),
        universe=universe,
        cost_model=transaction_cost_model_from_mapping(bt_params.get("costs")),
    )
    
    runner = BacktestRunner(
        config=config,
        calendar=calendar,
        importer=provider,
        strategy=strategy,
        risk_engine=risk_engine,
    )
    
    # 5. Run
    result = runner.run()
    
    # 6. Report
    print("\n" + "="*50)
    print("BACKTEST RESULTS")
    print("="*50)
    print(f"Total Return:   {result.metrics.total_return_pct:.2f}%")
    print(f"Max Drawdown:   {result.metrics.max_drawdown_pct:.2f}%")
    print(f"Win Rate:       {result.metrics.win_rate_pct:.2f}%")
    print(f"Sharpe Ratio:   {result.metrics.sharpe_ratio:.2f}")
    print(f"Total Trades:   {result.metrics.total_trades}")
    if result.daily_equity_curve:
        print(f"Final Equity:   {result.daily_equity_curve[-1]:.2f}")
    else:
        print(f"Final Equity:   {config.initial_capital:.2f}")
    print("="*50)
    
    if result.trades:
        print("\nLast 5 Trades:")
        for t in result.trades[-5:]:
            print(f"  {t.date} | {t.signal.name:4s} | {t.symbol:10s} | QTY: {t.quantity:4d} | PNL: {t.realized_pnl:.2f}")

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
    
    args = parser.parse_args()
    
    if args.command == "backtest":
        run_backtest(args)

if __name__ == "__main__":
    main()
