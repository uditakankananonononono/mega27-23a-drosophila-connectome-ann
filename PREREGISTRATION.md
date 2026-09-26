# PRE-REGISTRATION — LOCKED BEFORE OUTCOME INSPECTION

**Project:** mega27-23a — From Connectome to Computation
**Working title:** "From Connectome to Computation: mining the Drosophila FlyWire connectome for transferable architectural principles for artificial neural networks"
**Version:** v1.0 — locked 2026-09-26, before any hypothesis-relevant analysis was run on project data.
**Lock mechanism:** this file's SHA-256 hash is recorded in the first git commit of this repository (`PRE-REG LOCK` commit). Any later change ships as a versioned amendment with a stated reason; original text stays in history.

---

## 1. Central research question (user-specified, verbatim)

"Are there previously underused computational principles in the architecture of the Drosophila brain that can improve the efficiency, robustness, or learning ability of artificial neural networks?"

Framing: discovery-first. The project does NOT assume the fly brain is optimal for artificial tasks, and will not claim biological superiority without controlled evidence. Stage A discovers what is statistically unusual in the biological network; Stage C asks only whether those discovered structures perform a useful computational function.

## 2. Data (source-of-truth inventory; full ledger in DATA_INVENTORY.md)

Primary connectome: FlyWire FAFB v783 (Dorkenwald et al., Nature 2024), static release files from Zenodo record 10.5281/zenodo.10676866, downloaded 2026-09-26, each verified against the Zenodo-published MD5:
- `proofread_root_ids_783.npy` — 139,255 proofread neuron IDs (md5 e0e6c19732fd8c7a4e39a2d170105421) ✓ verified
- `proofread_connections_783.feather` — proofread neuron-neuron-neuropil connection table (md5 f48f972d262323a102aed49af1396b8a) — verification pending download
- `per_neuron_neuropil_count_pre_783.feather` (md5 90fcdb42c1ba05ed92820840fa1e6ba0) ✓ verified
- `per_neuron_neuropil_count_post_783.feather` (md5 bb5999f10920ade803d9f37097a43a56) — verification pending download

Graph definition (locked): nodes = the 139,255 proofread neurons; directed edge i→j = total synapse count across neuropils from i to j; analysis edge threshold = ≥5 synapses (the FlyWire consortium's standard strong-connection threshold, Dorkenwald et al. 2024). A parallel threshold sweep {1, 5, 10, 50} is run as a robustness check, not for picking a favorable threshold.

Secondary/annotation data (to be inventoried when obtained; each with URL + checksum):
- Neurotransmitter predictions (Eckstein, Bates et al. 2024) for excitation/inhibition analysis.
- Cell-type annotations (Schlegel et al., Nature 2024 consolidated hierarchy) for cell-type-stratified analysis.
- Task datasets for ANN experiments: MNIST, Fashion-MNIST (public mirrors, hash-recorded).

Accession convention (locked, stated honestly): an "accession" = one independently identified, hash-verified data unit ingested by the pipeline: each release file, each task dataset, and each per-neuropil derived subgraph (78 neuropils) used as a separate stratified analysis input. Padded or duplicate units do not count; the ledger lists every unit with its hash.

## 3. Stage A — biological principle discovery

Analyses (all computed on the thresholded directed weighted/unweighted graph):
A1. Directed triad census: counts of all 13 connected 3-node directed motif classes (MAN labels 003…300).
A2. Selected 4-node patterns: feedforward cascades and recurrent feedback chains (enumerated, not cherry-picked).
A3. Reciprocity (weighted and binary) vs null.
A4. Rich-club coefficient curve φ(k); hubs defined by degree percentile, not ad hoc.
A5. Community structure: Louvain modularity at resolution 1.0 (seeded, 25 restarts, best-of).
A6. Degree distributions (in/out, log-binned).
A7. E/I organization: fraction of inhibitory vs excitatory edges/neurons per Stage-B region using neurotransmitter predictions; sign-balance statistics.

Null models (locked, computed BEFORE any enrichment claim):
N1. Degree-preserving directed randomization: edge-swap Markov chain, 10 successful swaps per edge, 100 replicates.
N2. Matched-density directed Erdős–Rényi, 100 replicates.
Statistics: motif z-score vs null distribution (F1); a motif is declared ENRICHED only if significant under BOTH N1 and N2 after Benjamini–Hochberg FDR q=0.05 across all tested motif classes. Anti-enriched (suppressed) motifs are also reported. No outcome-dependent null selection.

## 4. Stage B — functional-region link

B1. Neuron→primary-neuropil assignment: neuropil with the largest pre+post synapse count per neuron (ties broken by pre count; documented).
B2. Neuropil-stratified motif enrichment: per-neuropil induced subgraphs (min 200 neurons to be testable), same nulls and FDR as Stage A.
B3. Locked hypothesis H2: motif enrichment profiles differ across neuropil functional classes (sensory/associative/motor); tested by permutation on neuropil class labels (10,000 permutations, p<0.05).
B4. Output: an explicit, written ranked list of candidate computational structures (motifs/organizational features), each tied to (a) significant enrichment and (b) the neuropil classes where it concentrates. This list is committed BEFORE Stage C training begins.

## 5. Stage C — translation to ANN architectures

C1. Mapping table (locked before training): each candidate structure from B4 → an explicit ANN wiring rule (e.g., 3-node feedforward loop → skip-gated sparse block; reciprocal pair → bidirectional coupled units; hub → high-fanout routing layer; E/I ratio → signed weights with fixed inhibitory fraction).
C2. Architectures (all feed-forward-capable, matched): 
- BASE-DENSE: conventional dense MLP.
- BASE-SPARSE: random sparse MLP at matched density.
- FLY-M: network wired from the top Stage-B motif set.
- FLY-MS: FLY-M plus signed E/I organization (built only if Stage A7 shows significant structure; otherwise noted as not built).
C3. Matching constraints: total trainable parameters within ±5% across architectures; per-layer fan-in/fan-out statistics recorded; FLOPs counted with a single fixed counting rule (F6).

## 6. Stage D — controlled experiments and gates

Tasks (fixed): T1 noisy MNIST (additive Gaussian noise, σ sweep 0/0.5/1.0/1.5); T2 Fashion-MNIST clean+noisy; T3 sequence prediction (adding problem, T=50); T4 learning-speed probe on permuted MNIST.
Protocol: ≥10 seeds per architecture×task; identical optimizer (Adam, lr 1e-3, batch 128), identical epoch budget, identical data splits; no architecture-specific tuning.
Locked gates:
- G1 (robustness): FLY-M noise-robustness AUC (F7) > BASE-SPARSE on T1/T2, paired-seed Wilcoxon p<0.05. 
- G2 (damage/ablation): under random neuron ablation at fractions {0,0.1,…,0.5}, FLY-M degradation slope (F8) shallower than BASE-SPARSE, p<0.05.
- G3 (efficiency): at matched accuracy (within 1 sd), FLY-M uses fewer parameters or FLOPs than BASE-DENSE, or better accuracy at matched budget (p<0.05).
Project-level success = at least 2 of {G1,G2,G3} passed with honest accounting. Failure of all gates = negative result, reported as such, with one documented redirect cycle inside this project (alternative motif set from B4 rank list) — never presented as a win.

## 7. Program-gate commitments

- ≥120 accession-level data units where meaningful (convention in §2; ledger in DATA_INVENTORY.md).
- ≥40 genuinely-executed external research tools/packages (each actually run in the pipeline; ledger in TOOLS_LEDGER.md; strict standard — no listed-but-unused).
- ≥10 numbered formulas (F1–F10+ defined in paper methods: z-score, reciprocity, rich-club, modularity, parameter count, FLOP count, robustness AUC, degradation slope, efficiency ratio, learning-speed measure, …).
- ~20-page paper, Times New Roman, embedded fonts, in paper/.
- Test suite (pytest) covering graph construction, null generation, motif census against brute-force counts, seed reproducibility, parameter-matching constraints, and gate arithmetic.

## 8. Blinding and anti-fishing rules

- This document is committed and hashed before any Stage A–D outcome is computed.
- No threshold, null, architecture, task, or gate may be altered after outcomes are seen, except via a written amendment that keeps the original text and states the reason.
- All negative results are reported. An invalidated intermediate result is quarantined and labeled, never silently dropped.

## 9. Environment

Python 3.10, numpy/pandas/pyarrow/networkx/scikit-learn (+ exact pinned versions in requirements.txt at analysis time). Seeds: master seed 23, per-experiment seeds derived deterministically and logged.

---

## AMENDMENT-1 (2026-09-26 4:11 PM IST) — user standing rules, verified verbatim

User WhatsApp 4:11:18 PM (verified verbatim in channel history): "...ask CHATGPT about more ideas like this that are highly advanced and can win isef. complete each project till now that i have given except the ones i asked to delete. and never count a negative as a result of a research project. make sure you have minimum 10 judging rounds about weaknesses in the project and what more to include to make it better."

Changes (original locked text above is preserved; this amendment governs where they conflict):
1. Section 6 "Failure of all gates = negative result ... one documented redirect cycle" is SUPERSEDED: failed gates trigger documented pivot cycles, and the project continues until a useful finding is reached. Honest negatives remain documented in the paper, but a negative result does not count as the project's result and does not end the project.
2. ChatGPT judge/ideation rounds are now part of this project: MINIMUM 10 rounds focused on weaknesses and missing content, each documented (round, critique summary, changes made) in JUDGE_ROUNDS.md. Statistical gates, null models, and locked analysis choices remain unchanged and are NOT influenced by judge suggestions after outcomes are seen; judges may only critique presentation, completeness, additional controls, and future pivots - never post-hoc gate redefinition.
3. The project goes to full completion (paper per PAPER_REQUIREMENTS.md + Drive deliverables).

---

## AMENDMENT-2 (2026-09-26 ~4:15 PM IST) — judge round 1 design repairs (pre-results)

Stage A outcomes are not yet final/committed at amendment time (null families still computing; no results reviewed). Judge round 1 (JUDGE_ROUNDS.md) surfaced design weaknesses; repairs below are locked BEFORE results are read. Original locked text preserved.

- A1. THIRD NULL FAMILY N3 (region-preserving): rewiring that preserves each neuron's in/out degree AND the primary-neuropil identity of both endpoints. Rationale (judge): degree-only shuffles destroy biological organization and can manufacture enrichment. N3 is applied to the whole-brain graph and within Stage B. Limitation stated honestly: the v783 static release carries no soma coordinates, so a truly spatial-coordinate null is impossible with current data; N3 is the region-level proxy. Enrichment claims that survive N1+N2 but not N3 are reported as "organization-dependent", separately from claims surviving all three.
- A2. Per-motif computational hypotheses: Stage C must state, for EACH candidate structure taken from B4, an explicit falsifiable computational hypothesis (what problem the structure solves) before its ANN variant is trained.
- A3. Null-count sensitivity: primary claims stay at the locked N=100 per family. An extended sensitivity arm (up to 1000 ER nulls; DP as compute allows) checks z-score stability for the key enriched classes; reported as sensitivity, not as a moved gate.
- A4. BH universe made explicit: FDR q=0.05 across the 16 motif classes within the whole-brain family; Stage B per-neuropil tests form a separate family; reciprocity, rich-club, modularity and NT-associated statistics are descriptive (with null comparisons) and carry no FDR claim.
- A5. Language: "predicted-neurotransmitter-associated organization" replaces "E/I organization" everywhere; no functional excitation/inhibition claim is made from predictions.
- A6. Rich-club: observed curve now compared against DP-null rich-club curves (same cutoffs).
- A7. Louvain: partition stability across the 25 seeded restarts quantified (variation of information); single-partition claims prohibited.

---

## AMENDMENT-3 (2026-09-26 ~6:20 PM IST) — seeded null implementations (pre-results)

Null-family z-scores/FDR had NOT been computed or read when this was written; only observed-graph stats and raw null census counts existed. The v3 runner was found to IGNORE per-null seeds in BOTH families (seed arguments computed but never passed; igraph's global RNG used), contradicting this document's master-seed reproducibility lock, and to need ~750s per DP null. Repairs:

- A8. Null generation moved to code/nulls.py (numpy, per-null seeds from SeedSequence(master_seed)); null DEFINITIONS unchanged (N1 DP: 10 successful simple endpoint swaps/edge; N2 ER: directed G(n,m)). DP rewire implementation is batched with conservative rejection (documented in code/nulls.py docstring). Verified: unit tests (exact degree preservation, simplicity, no loops, seed reproducibility - tests/test_nulls.py) and a real-graph benchmark (82.8s per 27M-swap rewire; invariants hold). Distributional cross-check vs igraph-rewire nulls (numpy DP census vs the 5 interim igraph DP null censuses) is PENDING and tracked as a Stage A finalization gate alongside the igraph census cross-check.
- A9. The interim unseeded nulls (100 ER + 5 DP) are DISCARDED, never analyzed; both families are rerun seeded. The v3 checkpoint is retained locally as stage_a_results_v3_unseeded.json for audit.
- A10. Observed Louvain modularity is recomputed with a seeded RNG; A7's 25-restart stability quantification follows Stage A.
- A11. Two-sided normal-approximation p-values from z, BH q over the 16-class universe per family (formalizes A4 for Stage A).
