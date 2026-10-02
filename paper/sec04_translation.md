# 4. From Structures to Architectures

## 4.1 Ranking candidate structures
Before any network was trained, the confirmatory motif results were turned into a ranked list of candidate computational structures (committed as B4, locked 2026-09-29). Only classes that survived all three nulls and were headline-safe under the mixing check could ground a candidate. The ranking was: (1) reciprocal pairs, (2) suppression of open chains, (3) the feedforward loop, (4) modular organization, and (5) clustered, non-distributed connectivity, which supports the first three and is not a separate arm. The cyclic triad and the eight mixing-unresolved classes were excluded, with reasons recorded.

## 4.2 A frozen mapping dictionary
Each candidate was paired with one falsifiable computational hypothesis and one allowed implementation, frozen before training (A17). Reciprocal coupling was hypothesized to improve robustness to input noise, chain suppression to shorten effective signal depth and speed learning, feedforward loops to filter transient noise, and modularity to localize damage. Alternatives that would have changed the claim, such as weight-tied reciprocals, a depth penalty in the loss, hand-wired isolated loops, or Louvain-partition modules, were rejected in writing. Louvain modules were rejected because Section 3.4 shows the partition is not stable.

The core implementation is a degree-stratified induced-adjacency mask. Neurons of the whole-brain export are sorted by total degree and cut into contiguous strata, one per layer, with one neuron mapped to one unit. The connectome's edges within and between strata become the sparse mask of a feed-forward network. Weights are independent and trained. This keeps the graph's reciprocal-edge and triad statistics, which a uniform random sparse graph at the same density does not.

## 4.3 Architectures and controls
All multilayer perceptrons share hidden sizes [256, 256, 128], Adam with learning rate 1e-3, batch size 128, and 15 epochs (30 for the sequence task). Parameter counts are matched within the multilayer-perceptron family. The reference counts are 300,938 weights for the 784-input tasks and 886,021 for the CIFAR-10 subset. The fly arms use about 1.5% density on the 784-input tasks, about 4.7 thousand weights in total.

The control ladder separates what each fly structure could be credited with:
- base_dense: dense network with the same layer shapes.
- base_sparse and ctrl_rand_sparse: uniform random masks at the same density, two independent draws.
- ctrl_er_sparse: Erdos-Renyi-distributed masks, controlling for degree heterogeneity.
- ctrl_dp_shuffled: masks from a degree-preserving shuffle of the fly graph, controlling for the degree sequence alone.
- small_cnn: a small convolutional reference, a locked exception to parameter matching.
- fly_m_c and ctrl_rand_sparse_c: connected-repair variants admitted before outcomes (Amendment 27), in which each mask is repaired to keep every unit connected at the exact edge count.
- fly_mod: a block-modular arm with an optic encoder, central routing and a classifier.

Tasks were noisy MNIST (T1, with noise levels 0, 0.5, 1.0 and 1.5), Fashion-MNIST (T2), a sequence adding task (T3), permuted MNIST as a learning-speed probe (T4), and a five-class CIFAR-10 subset (T5). All primary comparisons are paired by seed, 20 seeds per cell, using exact Wilcoxon tests.

## 4.4 Cost accounting
Cost uses a single fixed rule. Effective parameters count only mask-active weights, and effective FLOPs count two operations per active weight per example (F6, F7):

(F6)  P_eff = sum over layers of nnz(M_l)
(F7)  FLOPs_eff = 2 * P_eff

On the 784-input tasks, the sparse arms use about 9.5 thousand effective FLOPs against 600,576 for the dense network, a factor of about 63. The small CNN uses 497,056. Efficiency is reported as final accuracy per million effective FLOPs:

(F8)  E = acc_final / (FLOPs_eff / 10^6)

Section 6 reports what this ratio does and does not show.
