# 8. Audit Trail: Hypotheses, Gates and Outcomes

This section lists every preregistered hypothesis about the artificial networks in the order it was tested, with its outcome. It is a record, kept short, and the detailed numbers are in Sections 5, 6 and 6b.

| Test | Question | Outcome |
|---|---|---|
| G1, first wave | Does the fly-derived network beat a matched sparse baseline on noise robustness? | Not supported. Fly arm near chance on most tasks (noise-curve area 0.126). |
| G1, repaired (Amendment 27) | Same question after fixing reachability and matching the edge count exactly. | Not supported. Fly 0.264 against 0.590 for the matched control, 0 of 20 seeds, p = 1.9e-6. |
| G2 | Does the fly network lose accuracy more slowly under unit ablation than a matched random sparse network? | Supported within the sparse family. Retention-curve area 0.570 against 0.430 on noisy MNIST (15 of 20, p = 8.5e-4); 0.554 against 0.434 on permuted MNIST (17 of 20, p = 5.9e-4). |
| G3 | Does the fly network match dense accuracy at lower cost, or beat dense accuracy at matched budget? | Not supported. Dense and convolutional networks win in 20 of 20 seeds on four of five tasks. |
| G4 (Amendment 28) | Is the G2 graceful degradation specific to connectome wiring, or shared by dense and convolutional networks? | Not specific. Dense and convolutional networks retain far more accuracy (0.898 and 0.817 against 0.462 at 40% ablation). Within the sparse family the fly lead holds on noisy MNIST (18 of 20, p = 5.9e-4) and not on permuted MNIST (p = 0.62). |
| A29 | Does the fly network beat magnitude pruning at equal budget? | Not supported on accuracy (0 of 20 in all five conditions against layerwise pruning). Relative retention favors the fly network (17 of 20, Holm p = 5.2e-4 on noisy MNIST); absolute accuracy at 40% ablation ties. The global-pruning baseline collapsed and is excluded from the comparison. |
| A30, H30a | Does the fly mask beat a random mask when imposed on a pretrained network? | Not supported. Never better; one significant loss (noise level 1.0, Holm p = 3.8e-5). |
| A30, H30b | Does a half-fly, half-magnitude hybrid beat magnitude pruning? | Mixed. One borderline win (Fashion-MNIST, Holm p = 0.046, shared with the random-mask arm), two ties, two losses. |
| A30, H30c | Does the fly mask beat magnitude pruning on accuracy? | Not supported. Lost on four conditions (0 of 20), tied on one. |

One further preregistered element was not completed. A signed variant using predicted neurotransmitter signs (FLY-MS) was admitted before training but not built, because the predicted-sign export would have been needed, and it would otherwise duplicate the unsigned arm. Cell-type-preserving nulls (N4) were completed after a free public annotation source (ANN-001) was obtained; results are in Section 3.12.

What the ledger shows is one supported result and eight that are not or are mixed. The supported result is the narrow robustness statement of Section 5. No result in the ledger supports an accuracy or cost advantage for the connectome-derived design, and the paper claims none.
