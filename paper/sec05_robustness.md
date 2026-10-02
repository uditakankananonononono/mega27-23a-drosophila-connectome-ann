# 5. Results II: Relative Graceful Degradation Within the Sparse Family

## 5.1 Ablation protocol
Trained networks were damaged by removing a random fraction f of hidden units, with f in {0, 0.1, ..., 0.5}. The retention at fraction f is the accuracy at f divided by the same network's accuracy at f = 0, and the retention curve is summarized by its area:

(F9)  R(f) = acc(f) / acc(0)
(F10) AUC_R = integral over f of R(f) df, by the trapezoid rule.

The primary comparison pairs the connected-repair fly network against its matched random-sparse control by seed (20 seeds).

## 5.2 The fly mask degrades more gradually
On noisy MNIST, the fly network retained more accuracy than its matched random-sparse control at every damage level above 0.2 (fraction 0.3: 0.485 against 0.297, 14 of 20 seeds, p = 0.006; fraction 0.4: 0.462 against 0.208, 18 of 20, p = 9.5e-6; fraction 0.5: 0.343 against 0.168, 17 of 20, p = 4.8e-5). The retention-curve area was 0.570 for the fly network and 0.430 for the control (15 of 20 seeds, exact p = 8.5e-4). On permuted MNIST the same pattern held (retention-curve area 0.554 against 0.434, 17 of 20, p = 5.9e-4; retention at fraction 0.4 of 0.388 against 0.232, 16 of 20, p = 5.9e-4).

This is the project's one positive controlled result, and its scope is narrow. It is a statement about relative retention within a family of matched sparse networks. It is not a statement about absolute accuracy, and Section 6 shows that the effect does not extend to the dense or pruned baselines in absolute terms.

## 5.3 Which part of the wiring carries the effect
Two later comparisons narrow the interpretation. A dense network and a small CNN lose less in relative terms than any sparse network, so graceful degradation is not specific to connectome-derived wiring (Section 6.3). And when the fly mask was imposed on a network pre-trained dense and then fine-tuned, its retention was no better than that of a random mask (retention-curve area 0.468 against 0.468 on T1; Section 6.5). The retention advantage of the directly trained fly network is therefore best described as a property of that low-accuracy, edge-limited regime, not as an effect of the specific connectome edges.
