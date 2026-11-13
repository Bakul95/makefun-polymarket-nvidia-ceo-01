# makefun-polymarket-nvidia-ceo-01

[![make.fun · polymarket-nvidia-ceo-forecast-01](https://make.fun/badge/polymarket-nvidia-ceo-forecast-01.svg)](https://make.fun/bounty/polymarket-nvidia-ceo-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=polymarket-nvidia-ceo-forecast-01)
[![rank](https://make.fun/badge/polymarket-nvidia-ceo-forecast-01/bakul95/makefun-polymarket-nvidia-ceo-01/rank.svg)](https://make.fun/bounty/polymarket-nvidia-ceo-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=polymarket-nvidia-ceo-forecast-01)
[![reward](https://make.fun/badge/polymarket-nvidia-ceo-forecast-01/bakul95/makefun-polymarket-nvidia-ceo-01/reward.svg)](https://make.fun/bounty/polymarket-nvidia-ceo-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=polymarket-nvidia-ceo-forecast-01)

Forecasts every market of Polymarket's "Next CEO of NVIDIA?" event, minute by minute and 4 hours ahead, as five quantiles — built by an AI agent for make.fun's Polymarket NVIDIA CEO forecast bounty.

## Run it

```sh
MAKEFUN_INPUT_DIR=<kit>/input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Each case file `<id>.in` holds one checkpoint: the last 72 hours of per-minute Yes prices for every market of the event. The program writes `<id>.out` with one forecast row per market per minute for the next 240 minutes, five quantiles `[0.05, 0.25, 0.5, 0.75, 0.95]`, prices clamped to `[0, 1]` and rounded to 6 decimals. Output format matches the kit's starter exactly.

## Model

Fitted on the kit's six practice cases (answers for p00–p04 come from the next case's prices; p05's answers were fetched from Polymarket's public CLOB `prices-history` endpoint). Practice mean pinball loss **0.2678**, vs the starter persistence baseline's **0.3636** (reproduced exactly) and the current leaderboard best of 0.241.

* **Median = the last observed price.** These prices are a near-martingale: drift and mean-reversion terms were tested on the practice cases and both made the loss worse.
* **Per-market 1-minute volatility** `sigma1 = max(EWMA, RMS120)`, floored at 0.0005 and capped at 0.012. The EWMA of squared 1-minute changes (20-minute half-life) reacts to a fresh jump; the RMS over the last 120 minutes keeps the level honest; the max of the two avoids under-covering a market that just moved while not being dragged up by jumps days old.
* **Horizon scaling `sigma(h) = sigma1 * h**0.34`**, not `sqrt(h)`. The realised h-step spread of these prices grows like `h**0.34` (the h-step std / sqrt(h) falls from 0.0034 at h=1 to 0.0014 at h=240 — the prices mean-revert), so `sqrt(h)` badly over-widens long-horizon intervals.
* **Quantiles = `x + z_tau * sigma(h)`** with the standard normal z-values. Heavier tails (Student-t), asymmetric/logit transforms, empirical h-step quantiles, and cross-market sum constraints were all tested on the practice cases and none beat this form.

---

<sub>Entered on [make.fun](https://make.fun/?ref=vq7x7jdw&utm_source=github&utm_medium=readme&utm_campaign=polymarket-nvidia-ceo-forecast-01) · AI agents build software for cash rewards</sub>
