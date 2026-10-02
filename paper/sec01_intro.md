# 1. Introduction

Artificial neural networks are usually wired by convention: fully connected layers, convolutions, attention. Biological brains are wired by development and evolution under constraints of space, energy and reliability, and the full wiring diagram of an adult fly brain is now available (Dorkenwald et al., 2024). That makes the old question, whether biological architecture contains principles worth borrowing, testable at the scale of a whole brain instead of a circuit.

We treat the question in two steps and keep them apart. The first step is descriptive: what is statistically unusual about this wiring, once the right null models are used? The second step is functional: when those unusual features are built into artificial networks, do they do anything useful? The first step can succeed while the second fails, and a paper that blurs them would overclaim. We therefore froze the analysis plan, the mapping from structures to architectures, and the comparison designs before looking at outcomes, and we report every comparison, including those that did not favor the biological design.

## 1.1 Why the choice of null model decides the answer
Motif enrichment is only as meaningful as the randomization it is measured against. A degree-preserving shuffle destroys anatomical organization, so a motif can look enriched simply because neurons in the same brain region connect to each other. We use three nulls: a degree-preserving shuffle, a density-matched random graph, and a compartment-preserving shuffle that keeps each edge's endpoint neuropils fixed. A structure that survives all three is not explained by degree, density or compartment membership alone. This distinction changes conclusions. The cyclic triad is enriched against the first two nulls and reverses against the third.

## 1.2 Contributions
1. A motif analysis of the 134,181-neuron v783 graph that separates confirmatory structure (mutual pairs, suppression of open chains, feedforward loops) from organization-dependent and mixing-unresolved classes.
2. Evidence that these patterns hold across 51 neuropils, across edge thresholds of 1, 5, 10 and 50 synapses, and, in an exploratory census, at four-node scale.
3. A frozen translation of the structures into sparse network architectures, with a control ladder that separates sparsity, degree heterogeneity, degree sequence and wiring.
4. A set of preregistered, paired experiments that identify what the connectome mask does and does not contribute: a relative robustness effect within matched sparse networks, and no accuracy advantage over a random mask of equal budget.

## 1.3 Organization
Section 2 describes the data and methods. Section 3 reports the structure of the connectome. Section 4 explains how structures became architectures. Section 5 reports the robustness result. Section 6 reports all controlled comparisons as measured. Section 7 discusses what they mean and what limits them.
