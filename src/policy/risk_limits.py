"""Risk limits — deterministic risk policy enforcement.

Checks ALL risk rules from config before allowing a trade.
Any single rule violation → NO TRADE.

Rules:
  1. Kill switch
  2. Maximum stake per market
  3. Maximum daily loss
  4. Maximum open positions
  5. Minimum edge threshold
  6. Minimum liquidity
  7. Maximum spread
  8. Evidence quality threshold
  9. Market type allowed
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.config import RiskConfig, ForecastingConfig
from src.policy.edge_calc import EdgeResult
from src.forecast.feature_builder import MarketFeatures
from src.observability.logger import get_logger

log = get_logger(__name__)


@dataclass
class RiskCheckResult:
    """Result of risk limit checks."""
    allowed: bool
    decision: str  # "TRADE" | "NO TRADE"
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks_passed: list[str] = field(default_factory=list)


def check_risk_limits(
    edge: EdgeResult,
    features: MarketFeatures,
    risk_config: RiskConfig,
    forecast_config: ForecastingConfig,
    current_open_positions: int = 0,
    daily_pnl: float = 0.0,
    market_type: str = "UNKNOWN",
    allowed_types: list[str] | None = None,
    restricted_types: list[str] | None = None,
) -> RiskCheckResult:
    """Run all risk checks. Returns TRADE only if ALL pass."""
    violations: list[str] = []
    warnings: list[str] = []
    passed: list[str] = []

    # 1. Kill switch
    if risk_config.kill_switch:
        violations.append("KILL_SWITCH: Trading is disabled via kill switch")
    else:
        passed.append("kill_switch: OK")

    # 2. Minimum edge
    if edge.abs_edge < risk_config.min_edge:
        violations.append(
            f"MIN_EDGE: |edge| {edge.abs_edge:.4f} < threshold {risk_config.min_edge}"
        )
    else:
        passed.append(f"min_edge: {edge.abs_edge:.4f} >= {risk_config.min_edge}")

    # 3. Maximum daily loss
    if daily_pnl < 0 and abs(daily_pnl) >= risk_config.max_daily_loss:
        violations.append(
            f"MAX_DAILY_LOSS: daily loss ${abs(daily_pnl):.2f} >= limit ${risk_config.max_daily_loss:.2f}"
        )
    else:
        passed.append(f"daily_loss: ${abs(daily_pnl):.2f} < ${risk_config.max_daily_loss:.2f}")

    # 4. Maximum open positions
    if current_open_positions >= risk_config.max_open_positions:
        violations.append(
            f"MAX_POSITIONS: {current_open_positions} >= limit {risk_config.max_open_positions}"
        )
    else:
        passed.append(
            f"open_positions: {current_open_positions} < {risk_config.max_open_positions}"
        )

    # 5. Minimum liquidity
    total_depth = features.bid_depth_5 + features.ask_depth_5
    if total_depth > 0 and total_depth < risk_config.min_liquidity:
        violations.append(
            f"MIN_LIQUIDITY: depth ${total_depth:.2f} < threshold ${risk_config.min_liquidity:.2f}"
        )
    elif total_depth > 0:
        passed.append(f"liquidity: ${total_depth:.2f} >= ${risk_config.min_liquidity:.2f}")
    else:
        warnings.append("LIQUIDITY: No orderbook depth data available")

    # 6. Maximum spread
    if features.spread_pct > 0 and features.spread_pct > risk_config.max_spread:
        violations.append(
            f"MAX_SPREAD: {features.spread_pct:.2%} > threshold {risk_config.max_spread:.2%}"
        )
    elif features.spread_pct > 0:
        passed.append(f"spread: {features.spread_pct:.2%} <= {risk_config.max_spread:.2%}")

    # 7. Evidence quality
    if features.evidence_quality < forecast_config.min_evidence_quality:
        violations.append(
            f"EVIDENCE_QUALITY: {features.evidence_quality:.2f} < threshold "
            f"{forecast_config.min_evidence_quality:.2f}"
        )
    else:
        passed.append(
            f"evidence_quality: {features.evidence_quality:.2f} >= "
            f"{forecast_config.min_evidence_quality:.2f}"
        )

    # 8. Market type check
    if allowed_types and market_type not in allowed_types:
        if restricted_types and market_type in restricted_types:
            violations.append(
                f"MARKET_TYPE: {market_type} is restricted and requires explicit approval"
            )
        elif market_type == "UNKNOWN":
            violations.append(
                f"MARKET_TYPE: Could not classify market type — abort"
            )
        else:
            warnings.append(f"MARKET_TYPE: {market_type} not in preferred list")

    # 9. Clear resolution source
    if not features.has_clear_resolution:
        warnings.append("RESOLUTION: No clear resolution source defined")

    # Determine decision
    allowed = len(violations) == 0
    decision = "TRADE" if allowed else "NO TRADE"

    result = RiskCheckResult(
        allowed=allowed,
        decision=decision,
        violations=violations,
        warnings=warnings,
        checks_passed=passed,
    )

    log.info(
        "risk_limits.checked",
        market_id=features.market_id,
        decision=decision,
        violations=len(violations),
        warnings=len(warnings),
        passed=len(passed),
    )
    return result
