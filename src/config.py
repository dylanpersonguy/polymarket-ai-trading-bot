"""Shared configuration loader and Pydantic settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ScanningConfig(BaseModel):
    min_volume_usd: float = 5000
    min_liquidity_usd: float = 1000
    max_spread: float = 0.05
    max_days_to_expiry: int = 90
    categories: list[str] = Field(default_factory=list)
    batch_size: int = 50
    preferred_types: list[str] = Field(default_factory=lambda: ["MACRO", "ELECTION", "CORPORATE"])
    restricted_types: list[str] = Field(default_factory=lambda: ["WEATHER", "SPORTS"])


class ResearchConfig(BaseModel):
    max_sources: int = 10
    source_timeout_secs: int = 15
    primary_domains: dict[str, list[str]] = Field(default_factory=dict)
    secondary_domains: list[str] = Field(default_factory=list)
    blocked_domains: list[str] = Field(default_factory=list)
    min_corroborating_sources: int = 2
    search_provider: str = "serpapi"


class ForecastingConfig(BaseModel):
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096
    calibration_method: str = "platt"
    low_evidence_penalty: float = 0.15
    min_evidence_quality: float = 0.3


class RiskConfig(BaseModel):
    max_stake_per_market: float = 100.0
    max_daily_loss: float = 500.0
    max_open_positions: int = 10
    min_edge: float = 0.05
    min_liquidity: float = 500.0
    max_spread: float = 0.04
    kelly_fraction: float = 0.25
    max_bankroll_fraction: float = 0.05
    kill_switch: bool = False
    bankroll: float = 5000.0


class ExecutionConfig(BaseModel):
    dry_run: bool = True
    default_order_type: str = "limit"
    slippage_tolerance: float = 0.01
    limit_order_ttl_secs: int = 300
    max_retries: int = 3
    retry_backoff_secs: float = 2.0


class StorageConfig(BaseModel):
    db_type: str = "sqlite"
    sqlite_path: str = "data/bot.db"


class ObservabilityConfig(BaseModel):
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "logs/bot.log"
    enable_metrics: bool = True
    reports_dir: str = "reports/"


class BotConfig(BaseModel):
    scanning: ScanningConfig = Field(default_factory=ScanningConfig)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    forecasting: ForecastingConfig = Field(default_factory=ForecastingConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)


def load_config(path: str | Path | None = None) -> BotConfig:
    """Load config from YAML file, falling back to defaults."""
    if path is None:
        path = _PROJECT_ROOT / "config.yaml"
    path = Path(path)
    if path.exists():
        with open(path) as f:
            raw: dict[str, Any] = yaml.safe_load(f) or {}
        return BotConfig(**raw)
    return BotConfig()


def is_live_trading_enabled() -> bool:
    """Check if live trading is explicitly enabled via env var."""
    return os.environ.get("ENABLE_LIVE_TRADING", "").lower() == "true"
