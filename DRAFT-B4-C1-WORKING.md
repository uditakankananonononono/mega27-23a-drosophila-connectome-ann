> SUPERSEDED 2026-09-29 by B4_RANKED_CANDIDATES.md (locked) - retained for history only.

# WORKING DRAFT - NOT THE LOCKED B4 LIST / C1 MAPPING
Status: draft for finalization AFTER the N3 whole-brain arm lands (~10h).
The locked B4 ranked list and C1 mapping table will be committed before any Stage C
training, using the final three-null verdicts (N1+N2+N3) and the A26 mixing verdict.

## Inputs already final
- Stage A (N1 DP + N2 ER, 100+100 seeded): enriched vs both nulls - 102 (mutual pairs,
  z~+2845), 030T (feedforward loop, z~+638), 030C (z~+124); anti-enriched - 012 (single
  edges, z~-2877), 021D/U/C (open 2-paths, z~-390..-407). 003 +2843.
- A26 mixing verdict: 111D/111U/120C/120D/120U/201/210/300 = mixing-unresolved
  (excluded from headline claims); classes above are headline-safe.
- Stage B: whole-brain signature universal locally; 030T enriched in visual-pathway
  neuropils (ME_L/ME_R/GNG/LA_L), depleted in antennal lobes + EB.
- A7 Louvain: modularity 0.674-0.692, 261-265 communities, VI mean 1.22 (quality-stable,
  partition-variable - no single-partition claims).
- Reciprocity 0.1398 (descriptive, A4: no FDR claim).
- H2 permutation: class-level profiles NOT significantly different (p=0.299) - honest negative.

## Candidate structures (rank provisional; N3 may re-tier to "organization-dependent")
1. Reciprocal dyads (102) -> bidirectional coupled units (weight-tied or independent signed).
2. Feedforward loops (030T), concentrated in visual pathway -> skip-gated sparse FFL block.
3. Suppressed open chains (012/021x) -> wiring constraint: bounded chain depth, no long
   unbranched sequences (anti-pattern translated as a constraint, not a module).
4. Modular community structure (263 communities, Q~0.68) -> modular architecture:
   within-module dense-ish, between-module sparse bottlenecks.
5. Reciprocity 0.14 global -> fixed reciprocal-connection fraction in sparse init.

## C1 mapping table draft (per locked C1 examples; to be frozen in A17 dictionary)
| structure | wiring rule | rejected alternatives + rationale |
|---|---|---|
| 102 reciprocal pair | bidirectional coupled unit pair | weight sharing (too strong a claim); gating (adds params, breaks C3 match) |
| 030T FFL | 3-unit skip-gated sparse block (A->C direct + A->B->C) | simple skip connection (loses the 3-node motif constraint) |
| chain suppression | chain-depth cap in graph generator | none needed (constraint, not module) |
| modularity | K-module MLP with sparse inter-module routing | global sparse (loses community signal) |
| reciprocity fraction | fixed 14% reciprocal edge fraction in sparse init | learned symmetry (breaks C3) |

## Open items before freeze
- N3 survival verdicts (which of 1-5 remain Tier-1 confirmatory vs organization-dependent).
- FLY-MS build decision: A7 (E/I-organization Stage A item, distinct from Louvain A7 -
  naming collision in amendments; the E/I item is the neurotransmitter one, Tier 3) -
  NT predictions exist? check data inventory before Stage C.
- CIFAR-10-subset arm + shuffled-mapping controls (A15).
