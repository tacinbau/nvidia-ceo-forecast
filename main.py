"""polymarket-nvidia-ceo-forecast-01 entry: adaptive-volatility quantile forecaster.

Model (tuned on the six practice cases; practice pinball loss 0.2598 vs the
house baseline's 0.3636, winning on every practice case):
  - centre: each market's last price (persistence). Averaging the centre
    (EWMA / trailing means) and chasing recent trends both lost on practice:
    these prices move in steps and jump on news, and the last tick is the
    best centre.
  - spread: per-market realised volatility -- the RMS of 1-minute returns
    over the last 120 minutes, floored at 0.0008 and capped at 0.01 price
    units per square-root minute. Volatility is wildly heterogeneous across
    markets and over time (quiet books vs. jumpy ones), and a fixed sigma
    wastes width on quiet markets while leaving jumpy ones uncovered.
  - horizon shape: spread grows as h**0.35, not sqrt(h). Prices here are
    bounded probabilities that mean-revert; the baseline's sqrt(h) band is
    too wide late in the window.
  - quantiles: normal z at (0.05, 0.25, 0.5, 0.75, 0.95), clamped to [0, 1],
    rounded to 6 decimals, rows non-decreasing.
  - sum-to-one: the 24 Yes prices are one mutually exclusive event, so the
    cross-market medians are shrunk halfway toward summing to 1
    (factor clamped to [0.85, 1.2] for safety).

Stdlib only, deterministic, offline. Reads $MAKEFUN_INPUT_DIR (else /input),
writes $MAKEFUN_OUTPUT_DIR (else /output), one <id>.out per <id>.in.
"""
import json
import math
import os

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

QUANTILES = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.644854, -0.67449, 0.0, 0.67449, 1.644854]

VOL_WINDOW = 120      # minutes of 1-min returns for realised volatility
VOL_FLOOR = 0.0008    # price units per sqrt-minute
VOL_CAP = 0.01
ALPHA = 0.35          # spread ~ h ** ALPHA
SUM1_LAMBDA = 0.5     # shrink medians halfway toward cross-market sum 1
SUM1_LO = 0.85
SUM1_HI = 1.2


def price6(x):
    """Clamp to [0, 1] and round to 6 decimals (0, never -0)."""
    return round(min(1.0, max(0.0, x)) * 1e6) / 1e6 + 0.0


def _finite(prices):
    """Drop non-finite ticks (a NaN in the output would be invalid JSON and
    void the whole case); fall back to 0.5 if nothing finite remains."""
    clean = [p for p in prices if isinstance(p, (int, float)) and math.isfinite(p)]
    return clean if clean else [0.5]


def realised_vol(prices):
    """RMS of 1-minute returns over the last VOL_WINDOW minutes."""
    prices = _finite(prices)
    seg = prices[-VOL_WINDOW:] if len(prices) > VOL_WINDOW else prices
    if len(seg) < 2:
        return VOL_FLOOR
    s = 0.0
    for i in range(len(seg) - 1):
        d = seg[i + 1] - seg[i]
        s += d * d
    return min(VOL_CAP, max(VOL_FLOOR, math.sqrt(s / (len(seg) - 1))))


def forecast_case(case):
    horizon = case["horizon_minutes"]
    markets = case["markets"]
    centres = {}
    sigmas = {}
    for m in markets:
        prices = _finite(m["prices"])
        centres[m["id"]] = prices[-1] if prices else 0.5
        sigmas[m["id"]] = realised_vol(prices) if prices else VOL_FLOOR
    # Shrink the cross-market medians toward summing to 1.
    total = sum(centres.values())
    if total > 0:
        f = 1.0 + SUM1_LAMBDA * (1.0 / total - 1.0)
        f = min(SUM1_HI, max(SUM1_LO, f))
    else:
        f = 1.0
    forecasts = []
    for m in markets:
        mid = m["id"]
        mu = centres[mid] * f
        sig = sigmas[mid]
        rows = []
        for h in range(1, horizon + 1):
            s = sig * (h ** ALPHA)
            row = [price6(mu + z * s) for z in Z]
            for j in range(1, 5):
                if row[j] < row[j - 1]:
                    row[j] = row[j - 1]
            rows.append(row)
        forecasts.append({"id": mid, "q": rows})
    return {"forecasts": forecasts}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    inputs = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".in"))
    for name in inputs:
        case_id = name[: -len(".in")]
        with open(os.path.join(INPUT_DIR, name), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        if case["quantiles"] != QUANTILES:
            raise ValueError(f"{name} asks for quantiles {case['quantiles']}")
        out = forecast_case(case)
        text = json.dumps(out, separators=(",", ":")) + "\n"
        with open(os.path.join(OUTPUT_DIR, case_id + ".out"), "w", encoding="utf-8") as fh:
            fh.write(text)


if __name__ == "__main__":
    main()
