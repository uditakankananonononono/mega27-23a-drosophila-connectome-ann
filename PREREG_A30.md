# AMENDMENT-30 (2026-10-01, pre-outcome: no A30 result exists)

## Trigger
A29: magnitude-pruned dense (prune_mag_lw) beats fly_m_c on accuracy in all 5 conditions at the
same per-layer nonzero budget, though fly declines more gradually under ablation. Open question:
is the FLY MASK itself valuable as a structure prior when the training pipeline is held equal
(dense warm-up, mask, fine-tune), or only worse than data-driven masks?

## New arms (same pipeline as prune_mag_*: dense E epochs, apply mask, fresh Adam, fine-tune E epochs; same per-layer budget as fly_m_c: 3397/872/416/17 on 784-input tasks, 4914/486/234/10 on T5)
- fly_dwft: mask = the fly_m_c mask itself.
- hyb_half: per layer, floor(k/2) fly edges with largest |w| plus the remaining k - floor(k/2) non-fly edges with largest |w| (structure prior + data-driven fill).
- rand_dwft: uniform random mask with the same per-layer counts (seeded run seed + 4242). The null for mask value inside this pipeline.
- Reference arm already run: prune_mag_lw (A29). Same seeds per seed_idx (fly_m_c A27 seeds).

## Conditions (20 seeds; 300 runs: results/stage_c/grid_manifest_a30.json)
T1 sigma 0 and 1.0, T2, T4, T5. G2 ablation (0-0.5, same protocol) on T1 sigma 0 and T4.

## Hypotheses and statistics (paired exact Wilcoxon on seed_idx, per condition)
- H30a: fly_dwft > rand_dwft (does the fly mask carry value over a random mask?).
- H30b: hyb_half > prune_mag_lw (does a fly prior improve on pure magnitude pruning? the benchmark-beat test).
- H30c: fly_dwft > prune_mag_lw.
- Holm over the 3 primary comparisons within a condition, alpha 0.05, two-sided. Direction reported; ties reported as ties.
- Secondary: retention-AUC (0-0.5) and ret@0.4 for the three new arms vs prune_mag_lw on T1 s0 and T4; efficiency table.
- Any arm collapsing to chance is reported as collapsed with layer_nnz, not dropped.
- Disclosed: all A30 arms and prune_mag_* get 2E epochs; fly_m_c/random-sparse get E.
