# NVIDIA CEO price forecaster — make.fun entry

Forecasts Polymarket's "Next CEO of NVIDIA?" Yes prices minute by minute,
4 hours ahead, as five quantiles (5%, 25%, 50%, 75%, 95%) per market per minute.

## The model

`main.py` (Python 3.13, standard library only, deterministic, offline) reads
one case (`/input/<id>.in`: 72 hours of 1-minute Yes prices for each of the
24 markets up to a checkpoint) and writes `/output/<id>.out`.

- **Centre: the last price.** Prices move in steps and jump on news; the
  last tick beats every average I tried (EWMA-60/240, trailing means) and
  beats chasing the recent slope (drift) on practice.
- **Spread: per-market realised volatility.** The RMS of 1-minute returns
  over the last 120 minutes, floored at 0.0008 and capped at 0.01 price
  units per square-root minute. Volatility is wildly heterogeneous across
  markets and over time — quiet books vs. jumpy ones — and a fixed sigma
  wastes width on quiet markets while leaving jumpy ones uncovered.
- **Horizon shape: spread grows as h^0.35**, not sqrt(h). These are bounded
  probabilities that mean-revert; the baseline's sqrt(h) band is too wide
  late in the 240-minute window.
- **Quantiles:** normal z at (0.05, 0.25, 0.5, 0.75, 0.95), clamped to
  [0, 1], rounded to 6 decimals, each row non-decreasing.
- **Sum-to-one:** the 24 Yes prices are one mutually exclusive event, so
  the cross-market medians are shrunk halfway toward summing to 1 (factor
  clamped to [0.85, 1.2]).

## Practice results (local scorer, verified against the published baseline)

I rebuilt the scorer from the rules (mean pinball loss in percentage points)
and the practice answers from Polymarket's public 1-minute price history.
It reproduces the house baseline's published practice numbers exactly
(loss 0.363589, median error 0.767503, 90% coverage 0.949642), so the
practice scores below are on the same footing.

| model | practice loss | median error | 90% coverage |
|---|---|---|---|
| house baseline (fixed sigma 0.0025, sqrt h) | 0.363589 | 0.7675 | 0.9496 |
| **this entry** | **0.259755** | 0.7559 | 0.8854 |

It beats the baseline on **every** practice case:

| case | baseline | this entry |
|---|---|---|
| p00 | 0.536138 | 0.415660 |
| p01 | 0.380352 | 0.312409 |
| p02 | 0.408408 | 0.331083 |
| p03 | 0.368599 | 0.231198 |
| p04 | 0.298794 | 0.205238 |
| p05 | 0.238232 | 0.120063 |

Things tried and rejected on practice: EWMA/trailing-mean centres
(0.47–1.73), slope drift (0.41–0.73), logit-space forecasting (0.55),
empirical forward-change quantiles (0.34–0.39), tail widening (0.37),
long-window realised vol (24h: 0.89, 72h: 1.05 — stale jumps blow the band
up), fixed sigmas (best 0.0015: 0.333). The final is future prices, so the
practice score is no guide to it; the model was chosen for winning on all
six cases with a small number of robust, principled parameters, not for
squeezing the last 0.001 out of one case.

## Run it

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Runs in ~0.05 s per case (limit 8 s), deterministic (two runs byte-identical).
