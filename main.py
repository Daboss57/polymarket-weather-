"""CLI entrypoint for Polymarket weather backtesting."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from backtest.engine import BacktestEngine, MarketBacktestInput
from backtest.strategy import EdgeThresholdStrategy, StrategyConfig
from clients.openmeteo_client import OpenMeteoClient
from clients.polymarket_client import PolymarketClient
from config import DEFAULT_CONFIG
from contracts.models import Direction, MetricType, PricePoint, WeatherObservation
from contracts.parser import ContractParser
from data.storage import export_csv, export_json
from features.baseline_model import HistoricalBaselineModel, training_window
from utils.logging_utils import configure_logging

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DATA_DIR = BASE_DIR / "data"


def load_sample_price_history(path: Path) -> dict[str, list[PricePoint]]:
    payload = json.loads(path.read_text())
    parsed: dict[str, list[PricePoint]] = {}
    for token_id, rows in payload.items():
        parsed[token_id] = [
            PricePoint(
                timestamp=datetime.fromtimestamp(int(row["t"]), tz=timezone.utc),
                yes_price=float(row["p"]),
            )
            for row in rows
        ]
    return parsed




def load_sample_weather(path: Path) -> dict[str, list[WeatherObservation]]:
    payload = json.loads(path.read_text())
    parsed: dict[str, list[WeatherObservation]] = {}
    for location, rows in payload.items():
        parsed[location] = [
            WeatherObservation(
                date=datetime.fromisoformat(row["date"]).date(),
                max_temp_f=row.get("max_temp_f"),
                min_temp_f=row.get("min_temp_f"),
                precipitation_mm=row.get("precipitation_mm"),
            )
            for row in rows
        ]
    return parsed

def infer_resolved_yes(contract, observations) -> bool | None:
    target = next((obs for obs in observations if obs.date == contract.target_date), None)
    if target is None:
        return None
    if contract.metric_type == MetricType.DAILY_HIGH_F:
        if target.max_temp_f is None or contract.threshold is None:
            return None
        return target.max_temp_f >= contract.threshold if contract.direction == Direction.ABOVE else target.max_temp_f < contract.threshold
    if contract.metric_type == MetricType.DAILY_LOW_F:
        if target.min_temp_f is None or contract.threshold is None:
            return None
        return target.min_temp_f >= contract.threshold if contract.direction == Direction.ABOVE else target.min_temp_f < contract.threshold
    if contract.metric_type == MetricType.RAIN_YES_NO:
        if target.precipitation_mm is None:
            return None
        return target.precipitation_mm > 0.0
    return None


def run(args: argparse.Namespace) -> int:
    configure_logging(args.log_level)
    cfg = DEFAULT_CONFIG
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    cfg.cache_dir.mkdir(parents=True, exist_ok=True)

    polymarket_client = PolymarketClient(cfg.polymarket)
    weather_client = OpenMeteoClient(cfg.openmeteo)
    parser = ContractParser()
    model = HistoricalBaselineModel(seasonal_window_days=cfg.backtest.seasonal_window_days)
    strategy = EdgeThresholdStrategy(
        StrategyConfig(
            entry_edge=cfg.backtest.entry_edge,
            exit_edge=cfg.backtest.exit_edge,
            max_position_notional=cfg.backtest.max_position_notional,
        )
    )

    if args.sample:
        raw_markets = json.loads((SAMPLE_DATA_DIR / "sample_markets.json").read_text())
        markets = polymarket_client.parse_raw_markets(raw_markets)
        sample_prices = load_sample_price_history(SAMPLE_DATA_DIR / "sample_price_history.json")
        sample_weather = load_sample_weather(SAMPLE_DATA_DIR / "sample_weather.json")
    else:
        markets = polymarket_client.fetch_markets(limit=args.limit)
        markets = polymarket_client.filter_weather_markets(markets)
        sample_prices = {}
        sample_weather = {}

    backtest_inputs: list[MarketBacktestInput] = []
    for market in markets:
        normalized = parser.parse(market)
        if normalized is None:
            continue

        start, _ = training_window(normalized.target_date, cfg.backtest.lookback_years)
        if args.sample:
            history = sample_weather.get(normalized.location, [])
            history = [obs for obs in history if start <= obs.date <= normalized.target_date]
        else:
            coordinates = weather_client.resolve_location(normalized.location)
            if coordinates is None:
                continue
            history = weather_client.get_daily_observations(coordinates[0], coordinates[1], start, normalized.target_date)
        baseline = model.estimate(normalized, history)

        yes_token = next((t for t in market.tokens if t.outcome.strip().lower() == "yes"), None)
        if yes_token is None:
            continue

        price_history = sample_prices.get(yes_token.token_id) if args.sample else polymarket_client.fetch_yes_price_history(yes_token.token_id)
        if not price_history:
            continue

        resolved_yes = infer_resolved_yes(normalized, history)
        if resolved_yes is None:
            LOGGER.warning(
                "Skipping market %s: could not infer resolution for %s on %s",
                market.market_id,
                normalized.location,
                normalized.target_date,
            )
            continue
        backtest_inputs.append(
            MarketBacktestInput(
                market_id=market.market_id,
                fair_probability=baseline.probability_yes,
                price_history=price_history,
                resolved_yes=resolved_yes,
            )
        )

    engine = BacktestEngine(strategy)
    result = engine.run(backtest_inputs)

    trade_rows = [asdict(t) for t in result.trades]
    export_json(cfg.output_dir / "trades.json", trade_rows)
    export_csv(cfg.output_dir / "trades.csv", trade_rows)

    summary = asdict(result.summary)
    export_json(cfg.output_dir / "summary.json", [summary])

    LOGGER.info("Backtest complete: %s", summary)
    print(json.dumps(summary, indent=2, default=str))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Polymarket weather backtesting CLI")
    parser.add_argument("--limit", type=int, default=100, help="Max markets to fetch in live public mode")
    parser.add_argument("--sample", action="store_true", help="Run end-to-end with local sample market fixtures")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    return parser


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))
