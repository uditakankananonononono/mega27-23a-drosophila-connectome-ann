# 6. Controlled Comparisons Reported As Measured

Each comparison below was preregistered before its runs, uses 20 paired seeds, exact Wilcoxon tests, and Holm correction where several tests share a family. Results are given as measured, including those that did not favor the fly-derived networks. Stage C comprises about 2,400 trained runs.

## 6.1 Noise robustness against matched random sparse networks (G1)
On noisy MNIST, the area under the accuracy-versus-noise curve (trapezoid over noise levels 0 to 1.5) was 0.264 for the connected-repair fly network and 0.590 for its matched random-sparse control. The fly network won in 0 of 20 seeds (exact p = 1.9e-6). At zero noise the accuracies were 0.368 and 0.865, and at noise level 1.0 they were 0.205 and 0.488. The pattern held on Fashion-MNIST (0.409 against 0.808 at zero noise, 0 of 20, p = 1.9e-6). The hypothesis that reciprocal and feedforward-loop structure improves noise robustness is not supported. The directly trained fly mask learns more slowly and less accurately than a random mask of the same size: on learning-curve area it wins 0 of 20 on every task (p = 1.9e-6; Section 6.6).

## 6.2 Efficiency against dense and convolutional baselines (G3)
Dense and small-CNN networks beat every sparse arm in 20 of 20 seeds on four of the five tasks. On noisy MNIST the clean accuracies were 0.980 for the dense network, 0.989 for the CNN and 0.368 for the fly network. The sparse arms use about 4.7 thousand weights, 1.6% of the dense count. The cost saving is real, but it belongs to sparsity in general: matched random-sparse networks sit on the same cost-accuracy frontier or above it.

## 6.3 Ablation against dense and convolutional baselines (G4)
Dense and CNN networks degrade far more gracefully than any sparse network. At 40% unit ablation on noisy MNIST, retention was 0.898 for the dense network, 0.817 for the CNN and 0.462 for the fly network. Within the sparse family, the fly network retained more than the plain random-sparse baseline on noisy MNIST (18 of 20 seeds, p = 5.9e-4) and tied it on permuted MNIST (p = 0.62). Graceful degradation is therefore not specific to the connectome-derived mask.

## 6.4 Efficiency against magnitude pruning (A29)
Pruning a trained dense network by weight magnitude, with the fly network's own per-layer budget, gave accuracy above the fly network in all five conditions (noisy MNIST 0.758 against 0.368; 0 of 20 seeds for the fly network). A global-magnitude variant collapsed, with the output layer keeping zero to four weights and accuracy near chance. We report it as collapsed and do not count the fly network's wins against it. On relative retention-curve area the fly network beat the layerwise-pruned network (17 of 20, Holm p = 5.2e-4 on noisy MNIST; 17 of 20, p = 7.2e-5 on permuted MNIST), but at 40% ablation both sit near the floor in absolute terms (0.170 against 0.173).

## 6.5 The fly mask as a structure prior (A30)
The last preregistered test asked whether the fly mask carries value when it is imposed on a dense-pretrained network and then fine-tuned, with the same pipeline and per-layer budget as magnitude pruning. Three arms were compared: the fly mask, a hybrid of half fly edges and half magnitude-selected edges, and a random mask of the same budget (300 runs).
- Fly mask against random mask: never better. Noisy MNIST 0.502 against 0.574 (Holm p = 0.11); at noise level 1.0, 0.256 against 0.321, a significant loss (fly wins 1 of 20, Holm p = 3.8e-5); Fashion-MNIST p = 1.0, permuted MNIST p = 0.29, CIFAR subset p = 0.56.
- Fly mask against magnitude pruning: lost on four of five conditions, 0 of 20, Holm p = 5.7e-6, and tied on Fashion-MNIST (0.591 against 0.599).
- Hybrid against magnitude pruning: tied on noisy MNIST (0.7576 against 0.7583; 0.458 against 0.472 at noise 1.0), won on Fashion-MNIST (0.670 against 0.599, 14 of 20, Holm p = 0.046), and lost on the CIFAR subset (0.447 against 0.517, 3 of 20, Holm p = 9.5e-5). The Fashion-MNIST gain is shared by the random-mask arm (0.624), so it reflects a property of mask-then-fine-tune on that task, not of the fly edges.
- Retention-curve area on noisy MNIST was 0.468 for the fly-mask arm and 0.468 for the random-mask arm, against 0.423 for magnitude pruning (fly against magnitude, 14 of 20, p = 0.083).

## 6.6 Efficiency and learning speed
Per million effective FLOPs, sparse networks reach 40 to 90 points of accuracy on noisy MNIST, against 1.6 for the dense network and 2.0 for the CNN, because they use about 63 times fewer operations. Among sparse arms the fly network is the least efficient (38.8, against 91.4 for its matched random control, 80.1 for magnitude pruning). Learning speed, measured as mean accuracy over epochs, favors the matched random control over the fly network in 0 of 20 seeds on every task (p = 1.9e-6).

## 6.7 Summary of what Stage C supports
Three statements survive the controls. First, sparse networks cut cost by about 63 times at an accuracy price. Second, within matched sparse networks, a directly trained connectome-derived mask retains accuracy under ablation more gradually than a random mask, and that effect does not carry over to dense baselines or to the same mask imposed on a pretrained network. Third, the connectome's edges add no accuracy over a random mask of equal budget under any pipeline we tested. The results that stand independently of these comparisons are the structural findings of Section 3.
