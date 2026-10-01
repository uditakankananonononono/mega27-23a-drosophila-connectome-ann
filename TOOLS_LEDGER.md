# TOOLS LEDGER — genuinely executed external research tools (strict standard: only tools actually run in the pipeline appear here)

## Executed so far
1. curl (Zenodo/Codex data retrieval)
2. md5sum (checksum verification)
3. Python 3.10 runtime
4. numpy (array ops)
5. pandas (table ops)
6. pyarrow.feather (memory-mapped column reads)
7. python-igraph 1.0.0 (triad census, rewiring, ER nulls, communities)
8. networkx (brute-force triad reference in tests)
9. pytest (test suite)

## Planned (locked in PREREGISTRATION.md; added here only after actual execution)
scipy stats (Wilcoxon), scikit-learn, torch (Stage D ANN training), matplotlib (figures), ...

| 2026-09-29 | pyarrow/polars Tier-3 NT structure scan (proofread_connections_783.feather, 3.87M graph edges) | results/stage_b/nt_structure.json |
| 2026-09-29 | dp_rewire_c N3 within-neuropil null engine, Stage B Tier-2 (25 nulls x 51 neuropils) | results/stage_b/stage_b_n3.json |

## Verified-executed additions (2026-10-02; each imported/run by committed code with result files)
- polars (Tier-3 NT scan, Stage B), scipy (exact Wilcoxon, Holm inputs, in analyze_g3/g4/a29/a30), torch + torchvision (Stage C training, 2,400 runs), gcc (compiled dp_rewire_c.so, N3 null engine), ctypes (C engine binding), GitHub Actions (Stage C run grid), git (provenance).
- Not counted: scikit-learn, matplotlib, tqdm (listed in requirements, no committed executed use verified).
