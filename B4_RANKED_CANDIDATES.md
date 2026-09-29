# B4 — Ranked candidate computational structures (LOCKED 2026-09-29, before any Stage C training)

Ranking inputs: Tier-1 survival table (results/stage_a/tier1_survival.json), Stage B
stratification (results/stage_b/stage_b_summary.json), A7 Louvain stability
(results/stage_a/louvain_stability.json), A26 mixing verdict
(results/stage_a/mixing_verdict.json). Only Tier-1 confirmatory classes
(significant vs N1+N2+N3, BH q<0.05, headline-safe per A26) ground a candidate.

1. RECIPROCAL DYADS (motif 102). z_N3 = +1355 (Tier-1 confirmatory; z_N1 +2845).
   Stage B: mutual-pair enrichment in 45/51 neuropils (near-universal).
   Reciprocity 0.1398 (descriptive). -> C1: bidirectional coupled unit pairs.
2. OPEN-CHAIN SUPPRESSION (012 z_N3 -1355; 021D/U/C -280/-288/-282, Tier-1
   confirmatory). Universal across 47-51/51 neuropils. -> C1: bounded chain-depth
   wiring constraint (anti-pattern translated as constraint, not module).
3. FEEDFORWARD LOOP (030T). z_N3 = +132 (Tier-1 confirmatory; z_N1 +638).
   Stage B concentration: visual pathway (ME_L +205, GNG +200, ME_R +190, LA_L +49);
   depleted in antennal lobes and EB. -> C1: 3-unit FFL block in hidden layers.
4. MODULAR COMMUNITY ORGANIZATION. Q = 0.674-0.692 over 25 seeded restarts,
   261-265 communities (A7: quality-stable, partition-variable; no single-partition
   claim). Biological proxy for modules: neuropil assignment. -> C1/A22: block-modular
   architecture (optic encoder -> central routing -> classifier).
5. CLUSTERED (NON-DISTRIBUTED) CONNECTIVITY (003 z_N3 +1354 with 012 -1355):
   triads are either empty or closed; single-edge triads are suppressed. Supporting
   evidence for #1/#3/#4 (closed local structure over open). Not a separate arm.

EXCLUDED with reasons:
- 030C (3-cycle): organization-dependent (reverses to z_N3 = -65); enrichment was
  compartment-composition artifact. Within-compartment suppression noted as a finding.
- 111D/U, 120C/D/U, 201, 210, 300: mixing-unresolved (A26); no headline claims.
- H2 class-difference: NOT significant (p=0.299); no class-level architecture claim.
