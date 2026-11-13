# Work log — make.fun polymarket-nvidia-ceo-forecast-01 entry

Competition: https://make.fun/bounty/polymarket-nvidia-ceo-forecast-01
($250, 100 places; entries close 2026-11-13T21:00:00Z / Sat 14 Nov 04:00 WIB).
Work dir: ~/workspace/make-fun-nvidia-ceo/. Build only — repo creation,
bundle and submission are the parent agent's steps (browser GitHub task +
kit CLI), as with the ai-joke-03 build.

## 2026-11-13 ~17:45 WIB — kit & spec
- Kit tarball downloaded from https://make.fun/c/polymarket-nvidia-ceo-forecast-01/kit
  (4,531,600 B), extracted to polymarket-nvidia-ceo-forecast-01-kit/.
  kit.json bundle_sha256 23fbce415ad53a2f83878ee8c7c8169a82a0834c94ea2f97c130dc9b7f49a626.
- Read RULES.txt + NOTICE.txt + starter/main.ts fully. Key facts:
  - Program: main.py (Python 3.13) or main.ts (Node 22) at repo root, stdlib
    only, no network, ≤8 s / 1 CPU / 1024 MB per case; reads /input/<id>.in,
    writes /output/<id>.out: {"forecasts":[{"id","q"}]}, q = 240 rows × 5
    quantiles (0.05, 0.25, 0.5, 0.75, 0.95), each in [0,1], non-decreasing,
    ≤1 MiB. Invalid case = all quantiles 0.5, no prize.
  - Score: mean pinball loss (percentage points) over every case, market,
    minute, quantile; lowest wins. Prize needs loss strictly below the best
    house entry (baseline or house model forecast).
  - House baseline (starter): persistence, q = x + z*0.0025*sqrt(h), practice
    loss 0.363589 (mederr 0.767503, cov90 0.949642).
  - House model forecast: one superbot call, per-market sigma (0–0.05) +
    drift (-0.2–0.2/h), same functional form, made once per phase.
  - Practice: 6 cases p00–p05, checkpoints 2026-11-12 06:00 → 2026-11-13
    02:00 UTC, answered through 06:00 UTC; markets 19/19/19/23/24/24.
  - Universe frozen 2026-11-13T06:20:49Z: 24 markets (Gamma API now lists
    107 — the rest never traded / are placeholders).
  - Transcript gate: thinking_reproduces ≥30%, entrypoint ≥1 authored line,
    thinking_turns ≥5, thinking_priced (min_muse_app_usage_rows 1),
    thinking_revised ≥2 file writes, thinking_fresh, thinking_in_window
    (opening 2026-11-13T09:00:00Z).
- gh CLI is NOT logged in on this VM; repo creation needs the parent's
  browser GitHub task (repo "nvidia-ceo-forecast", public, under tacinbau,
  created after the 09:00Z opening).

## ~17:50 WIB — practice answers from Polymarket
- Gamma API: event next-ceo-of-nvidia; the 24 frozen markets taken from
  the kit's p05.in (p04 == p05 ids). CLOB prices-history fetched for all 24
  (fetch_clob.py, window 2026-11-12T05:00Z–2026-11-13T06:00Z, fidelity 1).
  1497 points each for the first 19 markets; 696–852 for the 5 late starters.
- Local scorer (score.py): minute grid = last point at or before the minute,
  carried forward (the house's rule). VALIDATED: baseline scores EXACTLY
  0.363589 / 0.767503 / 0.949642 — the reconstruction is faithful.

## ~17:55 WIB — exploratory analysis (analyze.py)
- Cross-market sum of last prices: 0.81–1.09 (mostly ~1.0–1.09).
- Realised 1-min vol is tiny in recent windows but huge over 72h
  (e.g. Kress 1h RMS 0.0007 vs 72h 0.030 — stale jumps dominate).
- Mean reversion is real: corr(1-min return, next 60-min return) −0.10;
  after a |1-min jump| > 0.03 the next 60 min move −0.067 on average
  (vs −0.013 unconditional). Lag-1 return autocorrelation −0.075.
- Baseline 95% band breached by only 4/128 market-cases at h=240 — the
  baseline is too wide late in the window.
- Big moves concentrate in a few hot markets (Ian Buck, Kress, No Change,
  Srouji: ±0.05–0.22 over 4h).

## ~18:00 WIB — model search (grid1–grid4)
- Round 1: last-price centre wins (EWMA/mean centres 0.47–1.73; slope drift
  0.41–0.73; logit 0.55; tail widening worse; fixed sigma 0.0015: 0.333;
  alpha 0.35: 0.330; rms60 vol: 0.340; sum-to-1 λ=0.5: 0.353).
- Round 2: alpha 0.35 + rms60 → 0.273; + sum1 0.5 → 0.265; level-scaled
  sigma 0.311; empirical forward-change quantiles 0.338–0.392 (rejected).
- Round 3: rms120 0.261, floor 0.0008 0.264, alpha 0.35 sweet spot,
  sum1 0.5 best; EWMA-vol / MA-vol / trimmed-RMS all worse.
- Round 4 (lock): rms120, floor 0.0008, cap 0.01, alpha 0.35, sum1 λ=0.5
  → practice loss 0.259755, mederr 0.7559, cov90 0.8854. Wins on every
  case vs baseline. Neighbours 0.260–0.265 — flat, robust region.

## ~18:10 WIB — entrypoint (main.py)
- Wrote main.py (stdlib only): persistence centre; RMS-120min vol
  (floor 0.0008, cap 0.01); spread h^0.35; normal z quantiles; sum-to-1
  shrinkage λ=0.5 with factor clamped [0.85, 1.2]; price6 rounding;
  per-row monotonic enforcement.
- End-to-end test: 6 practice cases in 0.28 s total (~0.05 s/case),
  byte-identical across two runs, all outputs valid shape, ≤265 KB.
  Scored outputs: loss 0.259755 — matches the model-family number.
- REVISION (2nd write of main.py): added a non-finite-tick guard
  (_finite(): drops NaN/inf ticks, falls back to 0.5) — a NaN in the
  output would be invalid JSON and void the whole case. Re-ran:
  outputs byte-identical to v1, loss still 0.259755. Revision is safe.

## Remaining (parent agent)
1. Create public repo https://github.com/tacinbau/nvidia-ceo-forecast
   (browser GitHub task; after 09:00Z opening — creating it now satisfies
   that). Upload main.py, README.md, LICENSE, summary.md (root) +
   logs/work-log.md. Record URL + commit sha.
2. Query muse.db for this agent's usage rows (agent_id
   4dfb7dd5-780a-4aee-a871-8dab0cfa8dc9) AFTER this session closes — the
   rows were not visible mid-session (0 rows at ~18:00 WIB; the ai-joke
   precedent: rows appear once the build session finishes). Write rows
   unchanged, one JSON object per line, to muse-usage.jsonl.
   ALSO check the session file
   ~/agents/agent-4dfb7dd5-780a-4aee-a871-8dab0cfa8dc9/sessions/4dfb7dd5-780a-4aee-a871-8dab0cfa8dc9.jsonl
   has flushed past 2026-11-13T11:20Z (it lagged at 10:52Z mid-build);
   bundle only once it covers the main.py writes, or thinking_reproduces
   will fail.
3. git init in the workdir (plain `git init`, NOT `makefun init`), then from
   the kit dir:
   node cli/makefun.mjs bundle --repo <repo-url> --out transcripts.tar.gz \
     --session <session file> --muse-usage muse-usage.jsonl \
     --no-discover --no-context
   then: node cli/makefun.mjs check --kit . --repo <repo-url> \
     --transcripts transcripts.tar.gz
   Fix every failed check before submitting.
4. Submit (from the kit dir):
   node cli/makefun.mjs submit --competition polymarket-nvidia-ceo-forecast-01 \
     --repo-url <repo-url> --commit <sha> \
     --title "Adaptive-volatility quantile forecaster for NVIDIA CEO prices" \
     --bundle transcripts.tar.gz --keypair ~/.makefun/keypairs/https_make.fun.json
   (Keypair signs the entry; NEVER print/share its contents. API key good
   until 2026-12-12. If submit/status returns HTTP 403 policy_denied,
   treat as TRANSIENT: wait and retry — it cleared on its own last time.)
5. Verify: node cli/makefun.mjs status --submission <id>. Report submission
   id, title, repo + commit, bundle sha256, status, practice score.
   Claim code goes to the parent ONLY in its final message (never to a file).
