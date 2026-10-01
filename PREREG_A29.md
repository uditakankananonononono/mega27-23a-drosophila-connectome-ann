# AMENDMENT-29 (2026-10-01, pre-outcome: no A29 run has been trained)

## Trigger
After G1-G4 (see JUDGE/amendment record): fly_m_c is the most ablation-robust SPARSE arm vs
random sparse (G2) but loses to dense and CNN on accuracy (G3) and robustness (G4). The
surviving question is within-budget structure value: at the SAME number of nonzero weights,
does the repaired fly wiring beat the standard way of obtaining a sparse network
(magnitude-pruning a trained dense MLP)?

## New arms (both use exactly fly_m_c's per-task nonzero-weight budget: 4,702 for 784-input
## tasks, 5,644 for T5; fly_m_c layer counts 3397/872/416/17 and 4914/486/234/10)
- prune_mag_lw: train the dense MLP (same hidden sizes, init, Adam lr 1e-3, batch 128) for E
  epochs (A17 budget), prune each layer to fly_m_c's layer-wise nonzero count by |w| (top-k),
  reset Adam, fine-tune E more epochs with the mask fixed. Same per-layer allocation as fly.
- prune_mag_gl: same, but keep the global top-k by |w| / mean|w_layer| across layers (total
  k = fly_m_c total; layer-mean normalisation prevents input-layer starvation from init
  scale; raw global magnitude at init zeroed the whole input layer in a pre-run unit check).
  This is the practitioner baseline (free layer allocation).
- Disclosed asymmetry: pruned arms receive 2E epochs total (dense phase + fine-tune); fly and
  random sparse arms receive E. This favours the pruned baselines (conservative against fly).
- Per-layer kept counts are recorded in each result JSON (layer_nnz).

## Conditions (20 seeds each, 200 runs: results/stage_c/grid_manifest_a29.json)
T1_mnist_noise sigma 0 and 1.0, T2_fashion 0, T4_permuted_mnist 0, T5_cifar10_subset 0.
T3 excluded. Seeds: fly_m_c's A27 seeds per seed_idx; comparison pairs by seed_idx with the
existing fly_m_c and ctrl_rand_sparse_c runs. G2 ablation (fractions 0-0.5, same protocol)
is run on T1 sigma 0 and T4 for the pruned arms (80 runs carry ablation).

## Hypotheses and statistics
- H29a (accuracy at matched budget): fly_m_c > prune_mag_gl and > prune_mag_lw on final val
  accuracy, per condition (5), paired exact Wilcoxon two-sided, Holm over the 2 references
  within a condition, alpha 0.05.
- H29b (robustness at matched budget): fly_m_c retention-AUC (ablation, 0-0.5) > each pruned
  arm on T1 sigma 0 and T4, same test and Holm.
- Ties (Holm p >= 0.05) are reported as ties; a loss is reported as a loss. A prune arm
  that collapses (zero-layer) is reported as collapsed with its layer_nnz, not dropped.
- Descriptive: efficiency table of accuracy vs effective params and effective FLOPs.
