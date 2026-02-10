"""Calibrator — adjusts raw LLM probabilities for better calibration.

Supports:
  - Platt scaling (logistic regression on historical forecasts)
  - Isotonic regression
  - No-op pass-through

For MVP, we use a simple heuristic calibrator that:
  1. Shrinks extreme probabilities toward 0.5
  2. Penalizes low-evidence forecasts
  3. Applies contradiction penalties
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from src.observability.logger import get_logger

log = get_logger(__name__)


@dataclass
class CalibrationResult:
    raw_probability: float
    calibrated_probability: float
    method: str
    adjustments: list[str]


def calibrate(
    raw_prob: float,
    evidence_quality: float,
    num_contradictions: int = 0,
    method: str = "platt",
    low_evidence_penalty: float = 0.15,
) -> CalibrationResult:
    """Calibrate a raw probability estimate.

    For MVP we use heuristic calibration:
      1. Shrink extremes (nothing is truly 0 or 1)
      2. Pull toward 0.5 when evidence is weak
      3. Pull toward 0.5 for each contradiction
    """
    adjustments: list[str] = []
    p = max(0.01, min(0.99, raw_prob))

    if method == "none":
        return CalibrationResult(
            raw_probability=raw_prob,
            calibrated_probability=p,
            method="none",
            adjustments=[],
        )

    # 1. Extremity shrinkage (logistic-style compression)
    if method == "platt":
        # Platt-like: apply slight logistic compression
        logit = math.log(p / (1 - p))
        # Shrink logit by 10% toward 0 (less extreme)
        shrunk = logit * 0.90
        p_shrunk = 1.0 / (1.0 + math.exp(-shrunk))
        if abs(p_shrunk - p) > 0.005:
            adjustments.append(f"extremity_shrinkage: {p:.3f} → {p_shrunk:.3f}")
            p = p_shrunk

    # 2. Low evidence penalty
    if evidence_quality < 0.4:
        penalty_weight = low_evidence_penalty * (1.0 - evidence_quality)
        p_penalized = p * (1 - penalty_weight) + 0.5 * penalty_weight
        adjustments.append(
            f"low_evidence_penalty (q={evidence_quality:.2f}): {p:.3f} → {p_penalized:.3f}"
        )
        p = p_penalized

    # 3. Contradiction penalty: pull toward 0.5
    if num_contradictions > 0:
        contradiction_weight = min(0.3, 0.1 * num_contradictions)
        p_contra = p * (1 - contradiction_weight) + 0.5 * contradiction_weight
        adjustments.append(
            f"contradiction_penalty (n={num_contradictions}): {p:.3f} → {p_contra:.3f}"
        )
        p = p_contra

    p = max(0.01, min(0.99, p))

    log.info(
        "calibrator.calibrated",
        raw=round(raw_prob, 4),
        calibrated=round(p, 4),
        method=method,
        adjustments=len(adjustments),
    )

    return CalibrationResult(
        raw_probability=raw_prob,
        calibrated_probability=p,
        method=method,
        adjustments=adjustments,
    )
