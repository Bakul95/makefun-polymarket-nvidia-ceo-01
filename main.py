#!/usr/bin/env python3
"""Forecast Polymarket's next NVIDIA CEO Yes prices, minute by minute, 4 hours ahead.

Reads each case file `<id>.in` from $MAKEFUN_INPUT_DIR (default /input) and writes
`<id>.out` to $MAKEFUN_OUTPUT_DIR (default /output), exactly like the kit's
starter (main.ts): one forecast row per market per minute, five quantiles
[0.05, 0.25, 0.5, 0.75, 0.95], prices clamped to [0, 1] and rounded to 6 decimals.

Model (fitted on the kit's six practice cases; practice pinball loss 0.2678
vs the starter persistence baseline's 0.3636):

* Median = the market's last observed price (a martingale: drift and
  mean-reversion terms were tested and hurt on the practice cases).
* Per-market 1-minute volatility sigma1 = max(EWMA of squared 1-minute
  price changes with a 20-minute half-life, RMS of the changes over the
  last 120 minutes), floored at 0.0005 and capped at 0.012. The max of a
  fast EWMA and a 120-minute RMS reacts to fresh jumps without being
  dragged up by jumps days old; the floor keeps quiet markets tight and
  the cap stops one big jump from blowing the intervals out.
* Horizon scaling sigma(h) = sigma1 * h**0.34, not sqrt(h). The realised
  h-step spread of these prices grows like h**0.34 (mean reversion: the
  h-step std / sqrt(h) falls from 0.0034 at h=1 to 0.0014 at h=240), so
  sqrt(h) badly over-widens the long-horizon intervals.
* Quantiles = x + z_tau * sigma(h) with the standard normal z-values.

Python 3.13 standard library only, no network, no third-party packages.
"""
import json
import math
import os

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

QUANTILES = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.6448536269514722, -0.6744897501960817, 0.0,
     0.6744897501960817, 1.6448536269514722]

ALPHA = 0.34          # horizon exponent: sigma(h) = sigma1 * h**ALPHA
FLOOR = 0.0005        # minimum 1-minute sigma (price units)
CAP = 0.012           # maximum 1-minute sigma (price units)
EWMA_HALFLIFE = 20.0  # minutes
RMS_WIN = 120         # minutes


def price6(x):
    """Clamp to [0, 1] and round to 6 decimals (0, never -0)."""
    v = round(min(1.0, max(0.0, x)) * 1e6) / 1e6
    return v + 0.0


def sigma1(prices):
    """Per-market 1-minute volatility from the price history."""
    # EWMA variance of 1-minute changes, 20-minute half-life.
    lam = 0.5 ** (1.0 / EWMA_HALFLIFE)
    var = 0.0
    for i in range(1, len(prices)):
        d = prices[i] - prices[i - 1]
        var = lam * var + (1.0 - lam) * d * d
    ewma = math.sqrt(var) if var > 0.0 else 0.0
    # RMS of the changes over the last RMS_WIN minutes.
    lo = max(0, len(prices) - RMS_WIN - 1)
    n = 0
    ss = 0.0
    for i in range(lo, len(prices) - 1):
        d = prices[i + 1] - prices[i]
        ss += d * d
        n += 1
    rms = math.sqrt(ss / n) if n else 0.0
    s = ewma if ewma > rms else rms
    if s < FLOOR:
        s = FLOOR
    elif s > CAP:
        s = CAP
    return s


def forecast(market, horizon):
    """One market's forecast: `horizon` rows of the five quantiles."""
    prices = market["prices"]
    if prices:
        x = prices[-1]
        s1 = sigma1(prices)
    else:
        x = 0.5
        s1 = 0.0025
    rows = []
    for h in range(1, horizon + 1):
        s = s1 * (h ** ALPHA)
        rows.append([price6(x + z * s) for z in Z])
    return rows


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    inputs = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".in"))
    for file in inputs:
        cid = file[: -len(".in")]
        with open(os.path.join(INPUT_DIR, file), "r", encoding="utf-8") as f:
            case = json.load(f)
        if case["quantiles"] != QUANTILES:
            raise SystemExit(
                "%s asks for quantiles %s, not %s"
                % (file, case["quantiles"], QUANTILES)
            )
        forecasts = [
            {"id": m["id"], "q": forecast(m, case["horizon_minutes"])}
            for m in case["markets"]
        ]
        with open(os.path.join(OUTPUT_DIR, "%s.out" % cid), "w", encoding="utf-8") as f:
            f.write(json.dumps({"forecasts": forecasts}) + "\n")


if __name__ == "__main__":
    main()
