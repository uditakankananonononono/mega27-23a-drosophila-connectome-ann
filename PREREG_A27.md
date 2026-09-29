# AMENDMENT-27 (2026-09-29, pre-outcome: no repair-arm training has run)

## Trigger
Stage C September wave (1,080 runs) showed G1 FAIL with a mechanical cause, verified by
mask autopsy: the A17 degree-stratified projection starves deep layers (fly_m: 5/10
outputs reachable, deep median fan-in 1-3; fly_mod: 0/10 reachable). ctrl_dp_shuffled
shows the same starvation (5/10), so the as-run test is non-informative about fly
structure: the projection, not the wiring, killed both fly and degree-matched control.

## New arms (A27)
- fly_m_c: the A17 fly_m projected masks UNION a minimal seeded random repair:
  for every layer, every row (unit) with zero fan-in receives exactly 2 distinct
  uniformly-sampled incoming edges (seed = run seed, stream per layer). This guarantees
  zero dead rows and full input->output reachability while preserving every fly edge.
- ctrl_rand_sparse_c: ctrl_rand_sparse masks + the SAME repair rule, then topped up with
  additional uniformly-sampled non-repair edges until its total edge count EQUALS the
  repaired fly_m_c count for the same layer dims (exact density match; control stays
  purely random structure).
- Both remain inside C3 (param count unchanged; masks only) and F5/F6 accounting uses
  effective (unmasked) counts as before.

## Pre-registered hypothesis and prediction
H27: fly-derived edges carry transferable inductive bias that is testable only once
projection connectivity starvation is removed.
P27 (G1-R): fly_m_c beats ctrl_rand_sparse_c on the G1 noise-robustness AUC
(T1_mnist_noise, sigmas 0/0.5/1.0/1.5, 20 seeds, paired Wilcoxon signed-rank p<0.05).
Secondary: same comparison on T2/T4 accuracy at sigma 0 and T3/T5 where applicable.
The September-wave result stands as the documented projection-sensitivity finding
(honest negative): naive connectome projection at brain sparsity is connectivity-starved.

## Grid
360 runs (2 arms x 9 task-conditions x 20 seeds), manifest results/stage_c/grid_manifest_a27.json,
same locked training protocol (A17 epochs/optimizer/splits). Seeds fresh (master-seed
derived, distinct from wave-1 streams). No other protocol element changes.
