# MLD Model — Reflection and Ideation (2026-10-13)

A "sit back and think it through again" pass after the synthetic probe revealed the model is
NOT actually locating the mixed layer. Repo-only working doc. Scope requested: narrow (within the
current CNN), wider (other ML methods), and diagnostics — what is likely to move the needle, or
whether to set this aside. Written to be actionable.

## What the evidence actually says (the honest diagnosis)

Two synthetic results dominate everything else:

1. **~6 m MAE on clean synthetic data, FLAT across every true depth z0** (6.1, 6.8, 5.9, 6.4,
   6.5, 5.9, 6.5 m from z0=20..80). On data built to have an unambiguous elbow, a working
   detector should hit ~1-2 m AND show structure (easier where the cline is sharp/mid-column,
   harder at the edges). Flat ~6 m everywhere is the signature of a model making a **broad,
   roughly population-centered guess** rather than finding each profile's elbow.

2. **No-MLD abstention ~2-3%.** On profiles built with NO mixed layer, the model emits a
   confident peak ~97% of the time. It has **not learned the abstain concept at all.**

These are the SAME failure wearing two hats: the model has learned to **always paint a plausible
low bump across the mid-column** and never commit hard to either a sharp peak or a flat line.
That strategy scores a mediocre-but-not-terrible BCE everywhere, which is exactly what gradient
descent will settle into if the loss lets it. The "95% coverage / ~5 m MAE on real data" we were
mildly pleased with was this same hedging behavior flattered by the real-data depth distribution.

**Conclusion:** this is not a "needs more tuning" situation. The current setup has a structural
reason to prefer hedging over detecting. That is good news — structural problems have structural
fixes, and the synthetic harness now lets us measure any fix against ground truth.

## Prime suspect: the loss + target design (not the architecture)

The architecture (4 conv layers, width 32, 1-wide heads) is small but adequate to find an elbow;
CNNs do this easily. The likely culprit is how we score it:

- **Per-bin BCE against a Gaussian-bump target, averaged over all 120 bins.** With ~116 "near-zero"
  target bins and ~4 "high" bins per profile, the loss is dominated by the many zero bins. The
  cheapest way to lower average BCE is to keep the whole curve LOW and SMOOTH — a diffuse blob
  beats a confident sharp peak that's occasionally in the wrong place (a wrong sharp peak is heavily
  penalized by the log term; a timid blob is penalized gently everywhere). So the loss actively
  **rewards hedging**. This single fact explains both symptoms.
- **No-MLD target = all zeros, same averaged BCE.** A profile that is "all zeros target" vs one
  with a bump differ in only ~4 bins out of 120 — ~3% of the loss. So the model has almost no
  gradient incentive to treat no-MLD differently from MLD-present. That is why abstention ~ 0.
- **Peak threshold 0.30 at read-out** turns any weak blob into a "detection," converting the
  hedging into near-100% false coverage.

## NARROW ideas — keep the heatmap-CNN, fix why it hedges

Ordered by expected impact / low effort. These are testable immediately against the synthetic set.

1. **Fix the class imbalance in the loss.** Weight the positive (bump) bins far more than the
   zero bins, or switch to a loss that doesn't average-dominate on background: **soft-argmax /
   expected-value regression** on the heatmap, or **focal loss**, or a **Gaussian-NLL** that
   rewards a confident narrow peak. Most direct: add a term that penalizes the DISTANCE of the
   predicted peak (soft-argmax) from the true depth — then a diffuse blob is no longer safe.
2. **Make "no MLD" a real signal, not 4 bins of difference.** Add an explicit **per-sensor
   presence head** (a scalar sigmoid "is there an MLD here?") trained with its own BCE, separate
   from the localization heatmap. Abstention becomes a learned decision with a full-strength
   gradient, instead of an emergent property of a nearly-flat heatmap. This likely fixes the 2%
   abstention outright.
3. **Sharpen the target / add a peakiness penalty.** Smaller Gaussian sigma (currently 4 m -> try
   2 m) makes the target more peaked; add a penalty on heatmap entropy/spread so the model must
   commit. Cheap knobs.
4. **Normalize the heatmap to a distribution (softmax over depth) + cross-entropy to the true
   bin.** This is the standard keypoint-localization recipe and structurally forbids the
   "low blob everywhere" solution because the output must sum to 1 — mass spent in the wrong place
   is mass taken from the right place. Strong candidate; a moderate rewrite of head + loss.
5. **Train longer with the stability fixes** (the thrash we never tamed): lower LR, early-stopping
   on the new peak-distance metric, more epochs. Likely secondary to 1-4 but cheap.

**My pick for first swing:** (2) presence head + (4) softmax-over-depth localization. Together they
map exactly onto the two failures (abstain + localize) and are the textbook fix. Measure on
synthetic; expect MAE to drop toward 1-2 m and abstention toward >80% if the diagnosis is right.

## WIDER ideas — other ML / non-DL methods

The humbling possibility: **a 1-D CNN may be overkill, and a classical method may beat it** on a
problem that is fundamentally "find the elbow in a monotone-ish curve."

6. **Classical/deterministic elbow detectors as a baseline AND a sanity ceiling.** Holte & Talley
   (already planned, Chuck) IS this. Also: max-gradient, max-curvature, the "Kneedle" algorithm,
   threshold methods. These have NO training, run instantly, and on clean synthetic data should
   crush 6 m MAE. **If a 3-line gradient-max detector gets ~1 m on synthetic, the CNN's value
   proposition collapses to robustness-on-noisy-real-data only** — which we must then prove it
   actually has. This is the single most clarifying experiment available and it is nearly free.
7. **Gradient-boosted trees / random forest on hand-engineered features** (max gradient depth,
   curvature peak depth, variance-change point, surface-to-depth deltas). Often matches deep nets
   on small tabular-ish problems with far less data and no hedging pathology; gives feature
   importances (interpretable — good for the trust story).
8. **1-D U-Net / segmentation framing** (per-depth "mixed vs not" classification). The boundary
   between the two classes IS the MLD; naturally yields a transition width; was in the original
   Analysis.md discussion. Handles ambiguity and no-MLD (all-"not-mixed") cleanly.
9. **Changepoint detection** (ruptures/PELT, Bayesian changepoint): the MLD is literally a
   changepoint in the gradient regime. Purpose-built, probabilistic (gives uncertainty), no training.
10. **Transformer / attention** — flagged earlier as the upgrade if noise is the hard part. But the
    synthetic data is CLEAN and the model still fails, so noise-robustness is NOT the current
    bottleneck. **Do not reach for a Transformer now** — it would add capacity to a model that
    isn't capacity-limited. Parked until a localization-capable model plateaus on noisy real data.

## DIAGNOSTIC ideas — see before deciding

11. **Look at predicted heatmaps on synthetic elbows (highest value, do first).** Dump/plot a
    handful: is the output a sharp peak at the wrong depth, or a diffuse blob? Sharp-but-wrong =>
    data/feature problem; diffuse blob => loss problem (confirms the hedging diagnosis above). One
    afternoon, decides which branch to pursue. (Extend inspector.py to point at synthetic, or a
    tiny heatmap-dump script.)
12. **Overfit-a-tiny-batch test.** Train on 10 synthetic profiles until near-zero loss; if the
    model CANNOT drive those to sharp correct peaks, the bug is architectural/loss, not data. The
    fastest "is the pipeline even capable" check in ML. Minutes to run.
13. **Classical-baseline number on synthetic (pairs with #6).** Gives the ceiling the CNN must beat
    to justify itself.
14. **Per-stratum error we already have** — extend to sharpness/elbow-radius strata, not just z0,
    to see if the model does better on sharp vs rounded elbows (it should, if it detects at all).

## What is likely to actually make a difference (bottom line)

- **Most likely to move the needle, lowest effort:** the diagnostic pair #11 + #12 (an afternoon),
  then the loss/target fix #2 + #4. The diagnosis strongly points at loss design; these address it
  head-on and are measurable against synthetic truth.
- **Most clarifying for the whole endeavor:** #6/#13 — a classical elbow detector on synthetic. It
  could reveal that the ML framing is unnecessary for the clean case and reframe the CNN's job as
  purely "robustness on messy real profiles," which we would then have to demonstrate deliberately.
- **Likely NOT the answer right now:** bigger models, Transformers, more channels, more data. The
  model fails on clean easy data, so it is not data-starved or capacity-starved — it is
  objective-misspecified.

## Recommendation given the clock

Time-boxed path (roughly a day of focused work), each step gated on the previous:
1. Heatmap dump on synthetic (#11) + tiny-batch overfit (#12) — confirm "loss hedging" diagnosis.
2. If confirmed: add presence head + softmax/soft-argmax localization (#2, #4), retrain, re-run
   eval_synthetic. Target: synthetic MAE < 2 m, abstention > 80%.
3. In parallel/cheap: classical elbow baseline on synthetic (#6) for the ceiling + the H&T comparison.

If step 2 does NOT get synthetic MAE under ~3 m with good abstention, **set the ML MLD aside** and
proceed with other project work — we would then have a clear, documented reason (objective fixes
tried, classical baseline available) rather than an open-ended "nothing helps." The synthetic
harness makes this a decidable question, which is itself the main gain from today.

## Diagnostic results (2026-10-13) — diagnosis CONFIRMED

Ran mld/diagnose.py on the filtered model:
- **(A) heatmaps are diffuse, not sharp.** Spread 5-12 m vs the 4 m target; peak heights low
  (0.2-0.76). When confident (ht~0.6) the peak IS near-correct (true 20.0 -> pred 20.5), proving
  the backbone CAN localize when it commits. When unsure (ht 0.2-0.3, spread ~12 m) it dumps a
  blob near ~11.5 m regardless of true depth — textbook hedging.
- **(B) tiny-batch overfit FAILS.** 12 profiles, 400 steps: loss plateaus at ~0.10 (not ~0),
  mean |pred-true| = 3.23 m (max 10.4 m). A capable objective drives a 12-example overfit to
  near-zero; this cannot. The **loss floor at 0.10 is the smoking gun** — BCE-vs-Gaussian-bump
  has a comfortable hedging minimum the model settles into.

**Verdict: the bug is the OBJECTIVE (loss/target), not data, capacity, or scale.** Fix = replace
the per-bin-BCE-vs-Gaussian with softmax-over-depth localization + an explicit presence head.
Instant test for any fix: it must drive the (B) tiny-batch overfit to <1 m.

### Fix implemented + VALIDATED (2026-10-13)

New objective (model.py): each head emits raw logits over depth; **softmax-over-depth +
cross-entropy to the true bin + a soft-argmax distance term** (localization, mass-conserving so
hedging is not free) and a **separate per-sensor presence head** (scalar BCE for abstain). New
`mld_loss`, `predict` decoder; old sigmoid-heatmap path retired.

Tiny-batch overfit gate (12 clean synthetic profiles):
- old objective: stuck, loss floor ~0.10, mean err 3.23 m.
- new objective, 400 steps: 1.97 m (still descending).
- new objective, 2000 steps: **0.98 m** — PASS. Loss kept falling (no plateau). One outlier
  profile at 7.4 m; LR 3e-3 jumpy (lower it for the real retrain).

Decision: PROCEED. Rewire train.py / eval_synthetic.py / infer.py / inspector.py to the
(loc_logits, pres_logits) API (old .pt checkpoints are obsolete — different architecture),
then full retrain + re-measure on synthetic (target: MAE < 2 m, abstention > 80%).

## Note on process (the Accountability Deficit)

This failure was only visible because of the synthetic ground-truth harness — the real-data
metrics (~5 m, 95% coverage) looked fine and hid it. That vindicates building the synthetic set
(Step 2 of the user's two-step accountability plan) BEFORE trusting the model. It also means the
"narrow/wide/diagnostic" choice above should be made against synthetic numbers, not real-data
numbers, from here on. See WorkingWithAgenticAI.md (slow walk-through; audit provenance/behavior,
not just the headline metric).
