# Polymarket Weather Backtester (v1)

Research-grade **backtesting-first** system for weather-threshold Polymarket markets.

## What this project does

- Fetches public Polymarket markets (no auth required)
- Filters weather-like contracts
- Parses contract text into structured measurable weather events
- Pulls historical weather observations from Open-Meteo
- Estimates baseline fair probabilities from historical seasonal hit rates
- Simulates deterministic YES-side backtests with simple entry/exit logic
- Exports results (`outputs/trades.csv`, `outputs/trades.json`, `outputs/summary.json`)

## Scope and assumptions

- **No live trading** implemented in v1
- Uses only public market data
- No fees/slippage/queue modeling yet
- Baseline model is **non-ML**, historical seasonal hit-rate only
- Contracts with ambiguous wording are rejected by parser

## Project structure

```text
.
├── main.py
├── config.py
├── requirements.txt
├── clients/
├── contracts/
├── features/
├── backtest/
├── data/
├── execution/
├── utils/
└── outputs/
```

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### 1) End-to-end sample run (recommended first)

This mode uses local market/price fixtures and live Open-Meteo weather history.

```bash
python main.py --sample --log-level INFO
```

### 2) Public API run

```bash
python main.py --limit 150 --log-level INFO
```

## Output artifacts

- `outputs/summary.json`: top-level stats (trades, win rate, average entry edge, realized PnL)
- `outputs/trades.json`: detailed trade records
- `outputs/trades.csv`: CSV export for analysis

## Backtest logic (v1)

- Compute fair probability from historical weather around target date (seasonal ± window days)
- Enter YES if `fair_prob - market_yes_price >= entry_edge`
- Optionally exit early if edge mean-reverts to `<= exit_edge`
- Otherwise settle at resolution (YES=1, NO=0)

## Next improvements

1. Add robust Polymarket schema adapters as API shapes evolve.
2. Add NWS/NOAA providers and an ensemble weather data abstraction.
3. Add better market resolution truth pipeline from explicit resolution sources.
4. Add transaction costs, slippage assumptions, and position sizing policies.
5. Add richer models (forecast-vs-climatology blend, Bayesian calibration).
6. Implement paper execution adapter and order/state management.

