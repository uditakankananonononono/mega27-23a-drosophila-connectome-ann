# 6b. Stage C in Detail: Every Arm, Every Task

Section 6 states the comparisons. This section gives the whole picture so that no arm is selected after the fact. All numbers are mean final validation accuracy over 20 seeds at zero added noise, from the committed result files (the sequence task, T3, is treated separately below).

| Arm | T1 MNIST | T2 Fashion | T4 permuted | T5 CIFAR-5 |
|---|---|---|---|---|
| base_dense | 0.980 | 0.887 | 0.980 | 0.638 |
| small_cnn | 0.989 | 0.906 | 0.962 | 0.745 |
| prune_mag_lw | 0.758 | 0.599 | 0.817 | 0.517 |
| ctrl_rand_sparse_c | 0.865 | 0.809 | 0.830 | 0.489 |
| hyb_half | 0.758 | 0.670 | 0.743 | 0.447 |
| rand_dwft | 0.574 | 0.624 | 0.568 | 0.287 |
| base_sparse | 0.571 | 0.535 | 0.508 | 0.241 |
| ctrl_er_sparse | 0.565 | 0.532 | 0.606 | 0.222 |
| ctrl_rand_sparse | 0.543 | 0.528 | 0.523 | 0.245 |
| fly_dwft | 0.502 | 0.591 | 0.534 | 0.274 |
| fly_m_c | 0.368 | 0.409 | 0.407 | 0.326 |
| prune_mag_gl (collapsed) | 0.228 | 0.707 | 0.297 | 0.200 |
| ctrl_dp_shuffled | 0.196 | 0.298 | 0.289 | 0.216 |
| fly_m | 0.139 | 0.180 | 0.204 | 0.200 |
| fly_mod | 0.114 | 0.100 | 0.114 | 0.200 |

## 6b.1 The first wave and its repair
The first full wave trained the unrepaired fly arms. Both the whole-brain arm (fly_m) and the modular arm (fly_mod) performed at or near chance on most tasks: fly_mod sits at 0.114 on MNIST, 0.100 on Fashion-MNIST and 0.200 on the five-class task, which are the chance levels of those tasks. The degree-preserving shuffled fly graph (ctrl_dp_shuffled) did poorly too (0.196 on MNIST), while the uniform sparse controls reached 0.54 to 0.57. That split is informative. A mask built by cutting a degree-sorted graph into layers inherits the graph's hub structure, which leaves many units with no incoming or no outgoing path in a small feed-forward network. Training cannot recover a unit that receives no input.

We diagnosed this as a reachability failure and, before looking at outcomes of the repaired wave, preregistered a repair (Amendment 27): reroute so that every output is reachable from the input, and match the edge count of the control exactly. The repaired arm (fly_m_c) and its matched control (ctrl_rand_sparse_c) were then trained for 360 runs. Repair raised the fly arm's noise-curve area from 0.126 to 0.264 and left it far below the matched control (0.590). The repair did what it was designed to do, since there are no dead rows and all ten outputs are reachable, and the fly arm is still worse. This is the second of two preregistered attempts at the noise-robustness hypothesis, and both failed.

## 6b.2 Task by task, fly against its matched control
The matched control beat the repaired fly arm in 20 of 20 seeds on noisy MNIST (0.865 against 0.368), on Fashion-MNIST (0.808 against 0.409; 0.528 against 0.275 at noise level 1.0), and on permuted MNIST (0.830 against 0.407); on the CIFAR subset the fly arm won 1 of 20 seeds (0.326 against 0.489, p = 3.8e-6). On the sequence task the two were tied (7 of 20, p = 0.13). The CIFAR task is the only one on which the sparse arms as a group sit close to each other (0.22 to 0.33 for most), because five-class CIFAR is hard for a multilayer perceptron with about 6,000 mask-active weights.

## 6b.3 Dense, convolutional and pruned baselines
The ordering at the top of the table is the same on every task: convolutional or dense networks first, and then, depending on the task, either magnitude pruning or the matched random control. On MNIST and permuted MNIST, pruning a trained dense network to the fly budget is the best sparse method (0.758 and 0.817). On Fashion-MNIST the matched random control is the best sparse method (0.809), well ahead of pruning (0.599) and the hybrid (0.670). Which mask wins therefore depends on the task, and the fly mask is not the winner on any of them.

## 6b.4 The collapsed baseline
Global magnitude pruning gave the output layer almost no weights: it kept between zero and four. That arm, prune_mag_gl, is at chance on MNIST (0.228), permuted MNIST (0.297) and the CIFAR subset (0.200), but 0.707 on Fashion-MNIST, where chance is 0.1. Some seeds survive and the arm is unstable. We report it in the table, and we do not count comparisons against it in the fly arm's favor. Against the per-layer pruned baseline, the fly arm lost in every condition except where noted in Section 6.4.

## 6b.5 What the controls isolate
The control ladder lets each possible explanation be separated. Sparsity alone costs a large amount of accuracy (base_sparse 0.571 against 0.980 for dense on MNIST). Degree heterogeneity alone (ctrl_er_sparse) changes little on MNIST (0.565 against 0.571) and is inconsistent elsewhere (0.606 against 0.508 on permuted MNIST, 0.222 against 0.241 on the CIFAR subset); we did not run a separate test of this contrast. The degree sequence of the connectome, carried by ctrl_dp_shuffled, is actively harmful in this construction (0.196), which says that the fly graph's hub-heavy degrees do not map well onto a small feed-forward network without repair. After repair, the fly arm recovers part of the loss (0.368) but the control built to the same edge budget does much better (0.865), so what remains of the gap is attributable to which edges the connectome chose, not to how many there are.

## 6b.6 Ablation and retention across all arms
Retention curves, normalized to each network's own accuracy at zero ablation, differ by family. At 40% ablation on noisy MNIST the dense network retained 0.898 of its accuracy, the small CNN 0.817, the fly arm 0.462, the matched control 0.208 and plain sparse 0.231. The retention-curve areas (trapezoid, 0 to 0.5) were 0.4745 (dense), 0.4509 (CNN), 0.2849 (fly), 0.2151 (control) and 0.2231 (sparse). On permuted MNIST they were 0.4754, 0.4491, 0.2768, 0.2170 and 0.2715. The fly arm leads the sparse family on retention on both tasks, but the dense and convolutional networks are well above all of them, and the fly arm's lead over plain sparse on permuted MNIST is small (0.277 against 0.272; the paired test found no difference). Absolute accuracy at high ablation is low for every sparse arm, since each starts from a low base.
