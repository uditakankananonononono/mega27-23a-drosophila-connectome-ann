# AMENDMENT-28 (2026-10-01, pre-outcome: no A28 run has been trained)

## Trigger
G2 (A27 amendment, run #7) found fly_m_c retains more accuracy under random hidden-unit
ablation than ctrl_rand_sparse_c (retention-AUC 0.570 vs 0.430, 15/20, p=8.5e-4). G3 showed
dense and CNN reference arms dominate on absolute accuracy and relative noise retention.
Open question: is fly's graceful ablation decay specific to the connectome topology, or a
generic property of sparse / low-accuracy models? Dense and CNN were never ablated.

## Design (frozen before any run)
- New arms ablated: base_dense, small_cnn, base_sparse (clean training, sigma 0).
- Tasks: T1_mnist_noise, T4_permuted_mnist (the two G2 tasks), 20 seeds each, seeds
  = each arm's own main-grid seeds per seed_idx (same convention as G2); pairing by seed_idx.
- Protocol: same as G2. Random hidden-unit ablation, fractions {0,.1,.2,.3,.4,.5}, applied
  after training, seeded per run. Unit = hidden neuron (MLPs) or conv channel (small_cnn).
  Same keep-vector generator recipe as ablation_eval (models.ablation_eval_generic).
- 120 runs: manifest results/stage_c/grid_manifest_g4.json (jobs 0,1). Run IDs carry '|abl|'.
- Metric (identical to G2): retention curve = acc(frac)/acc(0); retention-AUC = trapezoid
  over frac 0-0.5; per-fraction retention also reported (esp. 0.4).

## Hypotheses and statistics
- H28a: fly_m_c retention-AUC > each of base_dense, small_cnn, base_sparse, per task
  (paired exact Wilcoxon signed-rank on seed_idx, two-sided, Holm across the 3 references
  per task, alpha 0.05).
- Reading: if fly_m_c is higher than all three, graceful degradation is topology-linked and
  not generic sparsity or architecture; if dense or cnn match or exceed it, the claim narrows
  to "sparse arms trade peak accuracy" and is reported as such. Both outcomes are reported
  as-is; the G2 result stands either way.
- Also reported (descriptive): absolute accuracy at each fraction.
