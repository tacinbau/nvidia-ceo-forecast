# Summary — polymarket-nvidia-ceo-forecast-01 entry

Competition: "Forecast Polymarket's next NVIDIA CEO prices minute by minute,
4 hours ahead" — $250 total, 100 places (1st $40, 2nd $25, 3rd $15,
4th–10th $5, 11th–100th $1.50), USDC on Solana, escrow locked.
Entries close 2026-11-13T21:00:00Z (Sat 14 Nov 2026, 04:00 WIB).
Final: 12 checkpoints, 4h apart, 2026-11-13T21:00Z → 2026-11-15T17:00Z;
leaderboard within 7 days of the deadline.

## Entry

`main.py` — Python 3.13, stdlib only, deterministic, offline. Reads one
case (72h of 1-minute Yes prices for the 24 frozen-universe markets up to
a checkpoint), writes 240 minutes × 5 quantiles (0.05, 0.25, 0.5, 0.75, 0.95)
per market.

Model: persistence centre (last price) + per-market realised volatility
(RMS of 1-minute returns over the last 120 min, floor 0.0008, cap 0.01) +
spread growing as h^0.35 + normal quantiles + cross-market medians shrunk
halfway toward summing to 1 (factor clamped [0.85, 1.2]).

## Practice results (local scorer)

Scorer rebuilt from the rules (mean pinball loss, percentage points) with
answers fetched from Polymarket's public CLOB price history
(`data/clob/`, 24 markets, 2026-11-12T05:00Z–2026-11-13T06:00Z). It
reproduces the house baseline's published practice numbers EXACTLY
(loss 0.363589, median error 0.767503, 90% coverage 0.949642), which
validates the reconstruction.

| | loss | median error | 90% coverage |
|---|---|---|---|
| house baseline | 0.363589 | 0.7675 | 0.9496 |
| **this entry** | **0.259755** | 0.7559 | 0.8854 |

Per case (baseline → entry): p00 0.536→0.416, p01 0.380→0.312,
p02 0.408→0.331, p03 0.369→0.231, p04 0.299→0.205, p05 0.238→0.120.
Beats the baseline on all six cases. Runtime ~0.05 s/case (limit 8 s);
two runs byte-identical.

## What was tried and rejected (practice loss)

- Centres: EWMA-60 0.560, EWMA-240 1.727, mean-60 0.473, mean-240 0.535,
  mean-720 0.802 (last price wins).
- Drift from recent slope: 0.410–0.726 (trends do not persist at this scale).
- Logit-space: 0.553. Empirical forward-change quantiles: 0.338–0.392
  (noisy median). Tail widening ×1.2/×1.4: 0.368/0.374.
- Realised vol windows: 60 min 0.340, 360 min 0.393, 24h 0.889, 72h 1.052
  (stale jumps). Fixed sigma best 0.0015: 0.333; horizon exponent alpha
  0.35: 0.330 alone. Level-scaled sigma (sqrt(x(1−x))): 0.311.
- Final combination (rms120 + alpha 0.35 + sum-to-1 λ=0.5): 0.259755.
  Neighbouring settings sit at 0.260–0.265 — a flat, robust region, not a
  knife-edge fit. The practice is no guide to the final (rules say so);
  the model was picked for winning on every case with few parameters.

## Files

- `main.py` — the entrypoint (written, tested, then revised with a
  non-finite-tick guard; outputs byte-identical to the first version).
- `README.md`, `LICENSE` (MIT), `summary.md` (this file).
- `score.py` — local practice scorer (validates to the published baseline).
- `models.py`, `grid1.py`–`grid4.py`, `analyze.py` — model search.
- `fetch_clob.py`, `data/markets24.json`, `data/clob/*.json` — practice
  answers from Polymarket's public history.
- `polymarket-nvidia-ceo-forecast-01-kit/` — the kit tarball, extracted
  (kit.json bundle sha256
  23fbce415ad53a2f83878ee8c7c8169a82a0834c94ea2f97c130dc9b7f49a626).
- `logs/work-log.md` — build log.

## Status

Built and locally validated. NOT yet submitted: the public GitHub repo
`nvidia-ceo-forecast` under tacinbau still needs creating (browser GitHub
task), then bundle + check + submit via the kit CLI (see work log).
