"""Mechanical A17 freeze: compute reference params + fly-mask density per input shape
(pure numpy mirror of models.load_fly_masks projection, seed 0), write A17_FROZEN.json.
The scientific content is in A17_MAPPING_DICTIONARY.md / B4_RANKED_CANDIDATES.md."""
import json, os
import numpy as np

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..", "..")
H = [256, 256, 128]

def mlp_params(d, c):
    dims = [d] + H + [c]
    return sum(dims[i] * dims[i+1] + dims[i+1] for i in range(len(dims)-1))

def fly_density(d, c):
    """Mirror of models.load_fly_masks FROZEN RULE: degree-stratified strata, induced adjacency."""
    data = np.load(os.path.join(ROOT, "exports", "fly_graph_whole.npz"))
    src, dst, n = data["src"].astype(np.int64), data["dst"].astype(np.int64), int(data["n_nodes"])
    deg = np.bincount(src, minlength=n) + np.bincount(dst, minlength=n)
    order = np.argsort(deg)[::-1]
    dims = [d] + H + [c]
    strata, off = [], 0
    for dim in dims:
        strata.append(order[off:off + dim]); off += dim
    nnz = numel = 0
    for li in range(1, len(dims)):
        p, cu = strata[li - 1], strata[li]
        ip = np.zeros(n, bool); ip[p] = True
        ic = np.zeros(n, bool); ic[cu] = True
        nnz += int((ip[src] & ic[dst]).sum()); numel += len(cu) * len(p)
    return nnz / numel

ref = {"T1_mnist_noise": mlp_params(784, 10), "T2_fashion": mlp_params(784, 10),
       "T3_adding": mlp_params(100, 1), "T4_permuted_mnist": mlp_params(784, 10),
       "T5_cifar10_subset": mlp_params(3072, 5)}
dens = {"d784": fly_density(784, 10), "d100": fly_density(100, 1), "d3072": fly_density(3072, 5)}
arms_active = ["base_dense", "base_sparse", "fly_m", "ctrl_rand_sparse",
               "ctrl_dp_shuffled", "ctrl_er_sparse", "small_cnn", "fly_mod"]
a17 = {"frozen": "2026-09-29", "hidden_sizes": H,
       "epoch_budget": {"T1_mnist_noise": 15, "T2_fashion": 15, "T3_adding": 30,
                         "T4_permuted_mnist": 15, "T5_cifar10_subset": 15},
       "reference_params": ref, "reference_note": "MLP family only; small_cnn is a locked C3 exception (A17 doc)",
       "sparse_density_by_task": dens,
       "cifar10_subset_classes": [0, 1, 2, 3, 4], "cnn_channels": [16, 32],
       "graph_export_dir": "exports",
       "fly_wiring": {"fly_m": {"export": "fly_graph_whole.npz"},
                      "ctrl_dp_shuffled": {"export": "fly_graph_dp_shuffled.npz"},
                      "fly_mod": {"export": "fly_graph_modular.npz", "block_layer_map": [None, 0, 1, 1, None]},
                      "fly_ms_conditional": {"export": "fly_graph_whole.npz", "signs": None}},
       "fly_ms_enabled": False,
       "fly_ms_gate": "built only if the Tier-3 predicted-NT structure analysis shows structure (C2); not yet run",
       "arms_active": arms_active,
       "applicability": {"T3_adding": [a for a in arms_active if a != "small_cnn"]}}
json.dump(a17, open(os.path.join(HERE, "A17_FROZEN.json"), "w"), indent=1)
print("ref:", ref)
print("densities:", {k: round(v, 5) for k, v in dens.items()})
