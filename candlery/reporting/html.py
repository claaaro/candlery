"""Static HTML backtest tear sheet (Phase 1b)."""

from __future__ import annotations

import html
from datetime import date
from pathlib import Path

from candlery.backtest.runner import BacktestResult


def render_html_report(
    result: BacktestResult,
    *,
    title: str,
    start_date: date | None = None,
    end_date: date | None = None,
    universe_size: int | None = None,
) -> str:
    """Build a self-contained HTML document with metrics, equity curve, and trades."""
    m = result.metrics
    esc = html.escape

    period_rows = ""
    if start_date is not None:
        period_rows += f"<tr><th>Start</th><td>{esc(str(start_date))}</td></tr>"
    if end_date is not None:
        period_rows += f"<tr><th>End</th><td>{esc(str(end_date))}</td></tr>"
    if universe_size is not None:
        period_rows += f"<tr><th>Universe size</th><td>{universe_size}</td></tr>"

    initial = result.portfolio.initial_capital
    final_eq = result.daily_equity_curve[-1] if result.daily_equity_curve else initial

    metrics_rows = "\n".join(
        [
            f"<tr><th>Initial capital</th><td>{initial:,.2f}</td></tr>",
            f"<tr><th>Final equity</th><td>{final_eq:,.2f}</td></tr>",
            f"<tr><th>Total return</th><td>{m.total_return_pct:.2f}%</td></tr>",
            f"<tr><th>Max drawdown</th><td>{m.max_drawdown_pct:.2f}%</td></tr>",
            f"<tr><th>Win rate</th><td>{m.win_rate_pct:.2f}%</td></tr>",
            f"<tr><th>Sharpe (annualized)</th><td>{m.sharpe_ratio:.4f}</td></tr>",
            f"<tr><th>Total trades (fills)</th><td>{m.total_trades}</td></tr>",
        ]
    )

    chart_block = _equity_chart_svg(result.daily_equity_curve)

    trade_rows = []
    for t in result.trades:
        trade_rows.append(
            "<tr>"
            f"<td>{esc(str(t.date))}</td>"
            f"<td>{esc(t.symbol)}</td>"
            f"<td>{esc(t.signal.name)}</td>"
            f"<td>{t.quantity}</td>"
            f"<td>{t.price:.4f}</td>"
            f"<td>{t.realized_pnl:.2f}</td>"
            f"<td>{t.fees:.2f}</td>"
            "</tr>"
        )
    trades_body = "\n".join(trade_rows) if trade_rows else "<tr><td colspan='7'>No trades</td></tr>"

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{esc(title)} — Candlery</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #111; }}
    h1 {{ font-size: 1.5rem; }}
    table {{ border-collapse: collapse; margin: 1rem 0; width: 100%; max-width: 56rem; }}
    th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }}
    th {{ background: #f4f4f5; }}
    section {{ margin-bottom: 2rem; }}
    .chart-wrap {{ max-width: 56rem; overflow-x: auto; }}
  </style>
</head>
<body>
  <h1>{esc(title)}</h1>
  <p>Phase 1b static HTML report — Candlery backtest</p>

  <section>
    <h2>Run</h2>
    <table>
      {period_rows}
    </table>
  </section>

  <section>
    <h2>Performance</h2>
    <table>
      {metrics_rows}
    </table>
  </section>

  <section>
    <h2>Equity curve</h2>
    <div class="chart-wrap">
      {chart_block}
    </div>
  </section>

  <section>
    <h2>Trades</h2>
    <table>
      <thead>
        <tr><th>Date</th><th>Symbol</th><th>Signal</th><th>Qty</th><th>Price</th><th>Realized PnL</th><th>Fees</th></tr>
      </thead>
      <tbody>
        {trades_body}
      </tbody>
    </table>
  </section>
</body>
</html>
"""
    return doc


def _equity_chart_svg(equity: list[float], width: int = 720, height: int = 240) -> str:
    if len(equity) < 2:
        return "<p>Not enough equity observations to plot a curve.</p>"
    mn = min(equity)
    mx = max(equity)
    if mx == mn:
        mx = mn + 1e-9
    pad_x, pad_y = 12.0, 12.0
    inner_w = width - 2 * pad_x
    inner_h = height - 2 * pad_y
    n = len(equity)
    pts = []
    for i, v in enumerate(equity):
        x = pad_x + inner_w * (i / (n - 1))
        y = pad_y + inner_h * (1.0 - (v - mn) / (mx - mn))
        pts.append(f"{x:.2f},{y:.2f}")
    points_attr = " ".join(pts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'role="img" aria-label="Equity curve">'
        f'<rect width="100%" height="100%" fill="#fafafa"/>'
        f'<polyline fill="none" stroke="#2563eb" stroke-width="2" points="{points_attr}"/>'
        f"</svg>"
    )


def write_html_report(
    path: Path | str,
    result: BacktestResult,
    *,
    title: str,
    start_date: date | None = None,
    end_date: date | None = None,
    universe_size: int | None = None,
) -> None:
    """Write UTF-8 HTML report to *path* (parent dirs created if needed)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        render_html_report(
            result,
            title=title,
            start_date=start_date,
            end_date=end_date,
            universe_size=universe_size,
        ),
        encoding="utf-8",
    )
