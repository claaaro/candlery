# Candlery

Institutional-grade algorithmic trading platform focused on deterministic backtesting, risk-first architecture, and scalable system design.

---

## 🚀 Current Status

- Phase: **Phase 1a — Backtesting MVP (CLI)**
- Scope: **Equity EOD (NIFTY 50)**
- Data Source: **NSE Bhavcopy**
- Timezone: **UTC (internal)**

---

## 🧠 Architecture Principles

- Deterministic trading core (no AI in execution path)
- Risk-first system design
- Config-driven behavior (no hardcoding)
- Modular architecture (strategy / risk / data separation)
- AI-assisted development with structured state tracking

---

## 📁 Project Structure
```
src/ → Core system (data, strategy, risk, backtest)
config/ → Configurations (risk, exchange, universe)
docs/ → System design & specifications
tests/ → Unit tests
data/ → Local data (not committed)
```
---

## 🤖 AI Development Workflow

This project supports multi-platform AI development:

- Google Antigravity
- Cursor
- GitHub Copilot

All sessions MUST use:
```
docs/ai-state/
```

Start from:

- CURRENT_STATE.md
- TASK_QUEUE.md

---

## ⚠️ Important Rules

- Do NOT commit raw data
- Do NOT modify architecture without decision record
- Follow Phase 1 scope strictly (no intraday, no F&O)

---

## 📚 Documentation

See:

- docs/PROJECT_SPEC.md
- docs/DATA_STRATEGY.md
- docs/TIMEZONE_AND_MARKET.md
- docs/PHASE1_SCOPE.md

---

## 🏁 Getting Started

(Will be added after initial setup)

---

## 📌 Status

Repository bootstrapping in progress.
