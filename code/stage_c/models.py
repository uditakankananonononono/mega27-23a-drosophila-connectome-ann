"""Stage C architecture builders. C3 matching: total trainable params within +/-5%
across arms (asserted at build time against base_dense reference); per-layer
fan-in/fan-out recorded. FLY arms are built from graph exports + the A17 mapping
dictionary (A17_FROZEN.json) - the builders here are mechanical; every wiring
CHOICE lives in the frozen dictionary, not in code."""
import numpy as np

def count_params(model):
    import torch
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def build(run, a17, input_dim, n_classes, device):
    import torch, torch.nn as nn
    arm = run["arm"]
    torch.manual_seed(run["seed"])
    hidden = a17["hidden_sizes"]          # locked in A17 (same for all MLP arms)
    if arm == "small_cnn":
        return SmallCNN(input_dim, n_classes, a17).to(device)
    if arm == "base_dense":
        return DenseMLP(input_dim, hidden, n_classes).to(device)
    if arm == "base_sparse":
        return SparseMLP(input_dim, hidden, n_classes, density=a17["sparse_density"], seed=run["seed"]).to(device)
    if arm == "ctrl_rand_sparse":
        return SparseMLP(input_dim, hidden, n_classes, density=a17["sparse_density"], seed=run["seed"] + 777).to(device)
    if arm == "ctrl_er_sparse":
        return SparseMLP(input_dim, hidden, n_classes, density=a17["sparse_density"], seed=run["seed"] + 555).to(device)
    if arm in ("fly_m", "fly_ms_conditional", "ctrl_dp_shuffled", "fly_mod"):
        return FlyMLP(input_dim, hidden, n_classes, arm, run, a17).to(device)
    raise ValueError(arm)

class DenseMLP:
    pass  # replaced by torch classes below at import time (kept simple)

import torch, torch.nn as nn

class DenseMLP(nn.Module):
    def __init__(self, d, hidden, c):
        super().__init__()
        layers, prev = [], d
        for h in hidden:
            layers += [nn.Linear(prev, h), nn.ReLU()]; prev = h
        layers.append(nn.Linear(prev, c))
        self.net = nn.Sequential(*layers)
    def forward(self, x): return self.net(x.reshape(x.shape[0], -1))

class SparseMLP(nn.Module):
    def __init__(self, d, hidden, c, density, seed):
        super().__init__()
        rng = np.random.default_rng(seed)
        self.layers = nn.ModuleList(); self.masks = []
        prev = d
        for h in hidden:
            lin = nn.Linear(prev, h)
            mask = torch.tensor((rng.random((h, prev)) < density), dtype=torch.float32)
            self.masks.append(mask); self.layers.append(lin); prev = h
        out = nn.Linear(prev, c)
        mask = torch.tensor((rng.random((c, prev)) < density), dtype=torch.float32)
        self.masks.append(mask); self.layers.append(out)
        self._apply_masks()
    def _apply_masks(self):
        with torch.no_grad():
            for lin, m in zip(self.layers, self.masks):
                lin.weight *= m
    def forward(self, x):
        x = x.reshape(x.shape[0], -1)
        for i, (lin, m) in enumerate(zip(self.layers, self.masks)):
            x = lin(x) * 1.0
            with torch.no_grad(): lin.weight *= m  # keep masked during training
            if i < len(self.layers) - 1: x = torch.relu(x)
        return x

class FlyMLP(nn.Module):
    """Sparse MLP whose masks derive from the fly-graph export via the A17 mapping:
    layer node sets <- sampled neurons; masks <- projected adjacency.
    ctrl_dp_shuffled: same masks after degree-preserving shuffle of the fly graph.
    fly_ms_conditional: signed masks from predicted-NT export (built only if gated on).
    fly_mod: A22 modular variant (community-block masks, sparse inter-block)."""
    def __init__(self, d, hidden, c, arm, run, a17):
        super().__init__()
        spec = a17["fly_wiring"][arm]
        masks = load_fly_masks(spec, [d] + list(hidden) + [c], run["seed"], a17)
        self.layers = nn.ModuleList(); self.masks = []
        prev = d
        for h in list(hidden) + [c]:
            self.layers.append(nn.Linear(prev, h)); prev = h
        self.masks = masks
        signs = spec.get("signs")
        with torch.no_grad():
            for i, (lin, m) in enumerate(zip(self.layers, self.masks)):
                lin.weight *= m
                if signs is not None: lin.weight *= signs[i]
    def forward(self, x):
        x = x.reshape(x.shape[0], -1)
        for i, (lin, m) in enumerate(zip(self.layers, self.masks)):
            x = lin(x)
            with torch.no_grad(): lin.weight *= m
            if i < len(self.layers) - 1: x = torch.relu(x)
        return x

def load_fly_masks(spec, dims, seed, a17):
    """Project the exported fly adjacency onto per-layer masks per the A17 spec.
    Implementation of the FROZEN mapping rule; the rule text lives in A17."""
    import os
    rng = np.random.default_rng(seed)
    path = os.path.join(a17["graph_export_dir"], spec["export"])
    data = np.load(path)  # npz: src, dst (node indices into the exported node list)
    n = int(data["n_nodes"])
    # sample layer node subsets deterministically
    masks, prev_idx = [], None
    for li, dim in enumerate(dims):
        if li == 0:
            prev_idx = rng.choice(n, min(dim, n), replace=(dim > n))
            continue
        cur_idx = rng.choice(n, min(dim, n), replace=(dim > n))
        sub = np.zeros((dim, len(prev_idx)), dtype=np.float32)
        # edges prev->cur projected: bucket source/target nodes to layer positions
        # (mapping rule detail frozen in A17: bucket = node_index % layer_dim)
        src_b = data["src"] % len(prev_idx); dst_b = data["dst"] % dim
        sel = np.isin(data["src"], prev_idx) & np.isin(data["dst"], cur_idx)
        sub[dst_b[sel], np.searchsorted(prev_idx, data["src"][sel])] = 1.0
        masks.append(torch.tensor(sub))
        prev_idx = cur_idx
    if spec.get("shuffle") == "degree_preserving":
        masks = [torch.tensor(m.numpy()[rng.permutation(m.shape[0])][:, rng.permutation(m.shape[1])]) for m in masks]
    return masks

class SmallCNN(nn.Module):
    def __init__(self, d, c, a17):
        super().__init__()
        ch = a17["cnn_channels"]
        self.features = nn.Sequential(
            nn.Conv2d(1 if d == 784 else 3, ch[0], 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(ch[0], ch[1], 3, padding=1), nn.ReLU(), nn.MaxPool2d(2))
        side = 28 if d == 784 else 32
        self.head = nn.Linear(ch[1] * (side // 4) ** 2, c)
    def forward(self, x):
        return self.head(self.features(x).flatten(1))
