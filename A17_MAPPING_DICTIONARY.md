# A17 — Frozen mapping dictionary (LOCKED 2026-09-29, before any Stage C training; A2/A15/A17/A18/A19/A22)

Each B4 candidate -> one computational hypothesis (falsifiable) + ONE allowed
implementation + rejected alternatives. No architecture may change after training starts.

## M1. Reciprocal dyads -> bidirectional coupled unit pairs (B4 #1)
Hypothesis: reciprocal coupling lets neighboring units cross-check inputs, improving
robustness to input noise (falsified if FLY-M does not beat controls on T1/T2, G1).
Implementation: masks = induced adjacency among degree-stratified node strata of the
whole-brain export (FROZEN RULE: nodes sorted by total degree, contiguous strata per
layer, 1-1 node->unit). Hub-rich strata keep masks trainable (~1.5% density); the
strata rule preserves the graph's reciprocal-edge and triad statistics far better
than a uniform random sparse graph at matched density. Weights independent (signed
by init).
Rejected: weight-tied reciprocals (stronger claim than the data supports); gated
recurrence (adds parameters, breaks C3 match; becomes an RNN).

## M2. Chain suppression -> bounded-depth mask generator (B4 #2)
Hypothesis: suppressing long unbranched paths shortens effective signal depth,
improving learning speed (falsified on T4 if no advantage).
Implementation: same degree-stratified induced-adjacency masks (the exported graph
empirically lacks long open chains; uniform random sparse controls do not).
Rejected: explicit depth penalty in the loss (changes the objective, not the wiring).

## M3. FFL -> 3-unit feedforward-loop block (B4 #3)
Hypothesis: coherent FFLs act as persistence detectors, filtering transient noise
(falsified on T1 sigma sweep if FLY-M noise AUC <= controls, G1).
Implementation: same degree-stratified induced-adjacency masks (local triad
statistics conserved by stratification); visual-pathway concentration motivates the
fly_mod optic encoder block.
Rejected: hand-wired isolated FFL modules (breaks parameter matching; no longer
graph-derived).

## M4. Modularity -> neuropil-block modular arm, A22 (B4 #4)
Hypothesis: community structure localizes damage, improving ablation resilience
(falsified on G2 if degradation slope not shallower).
Implementation: fly_mod: optic-block encoder -> central-block routing -> classifier,
masks from fly_graph_modular.npz with degree-stratified strata within each block
(block_layer_map [None, 0, 1, 1, None]).
Rejected: Louvain-partition modules (A7 prohibits single-partition claims; neuropils
are biological ground truth, partitions are inferential).

## Controls (A18 ladder) and their exact meaning
- base_dense: dense MLP, same layer shapes. Reference for params/FLOPs (C3, F5/F6).
- base_sparse: uniform random sparse masks at the SAME effective density as FLY-M
  (density computed per input shape in A17_FROZEN.json). Controls for sparsity alone.
- ctrl_rand_sparse: second independent random sparse draw (controls for a lucky mask).
- ctrl_er_sparse: ER-distributed sparse masks (controls for degree heterogeneity).
- ctrl_dp_shuffled: masks from a degree-preserving shuffled fly graph (export
  fly_graph_dp_shuffled.npz, C-engine rewire 10 swaps/edge, seed 260000). Controls for
  degree sequence alone - destroys motif/community structure.
- small_cnn: small CNN reference point. EXPLICIT C3 EXCEPTION (locked here): a small
  CNN cannot reach MLP parameter counts without ceasing to be small; it is a
  task-baseline control, excluded from G3's +-5% param-matching assertion.

## Conditional arm
- fly_ms_conditional (signed E/I masks from per-connection NT predictions): gated on
  the Tier-3 predicted-NT structure analysis (not yet run). fly_ms_enabled=false in
  A17_FROZEN.json until that analysis lands and shows structure; otherwise recorded
  as not built (C2). No functional E/I claim from predictions (A5).

## Causal/ablation arms (A15/A19, phase 2 after base grid)
- G2 damage: random neuron ablation {0,0.1,...,0.5} on trained models.
- A15 motif knockout: remove reciprocal-derived mask edges from FLY-M (necessity test).
- A19 causal triangle: (A) fly-derived = fly_m, (B) topology-preserved randomized =
  ctrl_dp_shuffled, (C) B + reciprocal edges reinserted. Positive requires A>B,
  knockout damages A specifically, C partially recovers. >=20 seeds per condition.
- A15(c) shuffled-mapping control: B4->wiring table with randomly permuted
  structure->rule assignment, same generator (benchmarks the subjective mapping).

## Locked config values (in A17_FROZEN.json)
hidden_sizes [256,256,128]; epochs 15 (T1/T2/T4/T5), 30 (T3); T5 = CIFAR-10 classes
[0,1,2,3,4]; optimizer Adam lr 1e-3 batch 128 (S6); T3 excluded from small_cnn
(non-image task). Everything else per PREREGISTRATION.md.
