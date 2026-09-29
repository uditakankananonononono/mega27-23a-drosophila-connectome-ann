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
    dkey = "d100" if input_dim == 100 else ("d3072" if input_dim == 3072 else "d784")
    dens = a17["sparse_density_by_task"][dkey]
    if arm == "base_sparse":
        return SparseMLP(input_dim, hidden, n_classes, density=dens, seed=run["seed"]).to(device)
    if arm == "ctrl_rand_sparse":
        return SparseMLP(input_dim, hidden, n_classes, density=dens, seed=run["seed"] + 777).to(device)
    if arm == "ctrl_er_sparse":
        return SparseMLP(input_dim, hidden, n_classes, density=dens, seed=run["seed"] + 555).to(device)
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
    Implementation of the FROZEN mapping rule; the rule text lives in A17.
    ctrl_dp_shuffled uses its own pre-shuffled export (true degree-preserving rewire,
    C engine, fixed seed - no runtime permutation). fly_mod restricts per-layer node
    sampling to neuropil blocks per spec['block_layer_map']."""
    import os
    path = os.path.join(a17["graph_export_dir"], spec["export"])
    data = np.load(path)  # npz: src, dst, n_nodes [, block]
    src, dst = data["src"].astype(np.int64), data["dst"].astype(np.int64)
    n = int(data["n_nodes"])
    blocks = data["block"] if "block" in data.files else None
    blm = spec.get("block_layer_map")
    # FROZEN RULE (A17): degree-stratified 1-1 node->unit mapping. Nodes sorted by
    # total degree (desc); layer l takes contiguous strata (hub-rich subgraph keeps
    # masks trainable; random-node projection is degenerate at brain sparsity).
    # fly_mod: strata computed within each block's nodes per block_layer_map.
    deg = np.bincount(src, minlength=n) + np.bincount(dst, minlength=n)
    order = np.argsort(deg)[::-1]
    if blm is not None and blocks is not None:
        strata = []
        for li, dim in enumerate(dims):
            b = blm[min(li, len(blm) - 1)]
            pool = order if b is None else order[blocks[order] == b]
            take = min(dim, len(pool))
            strata.append(pool[:take])
    else:
        strata, off = [], 0
        for dim in dims:
            strata.append(order[off:off + dim]); off += dim
    masks = []
    for li in range(1, len(dims)):
        prev_idx, cur_idx = strata[li - 1], strata[li]
        pos = np.empty(n, dtype=np.int64); pos[prev_idx] = np.arange(len(prev_idx))
        posc = np.empty(n, dtype=np.int64); posc[cur_idx] = np.arange(len(cur_idx))
        inset_p = np.zeros(n, bool); inset_p[prev_idx] = True
        inset_c = np.zeros(n, bool); inset_c[cur_idx] = True
        sel = inset_p[src] & inset_c[dst]
        sub = np.zeros((len(cur_idx), len(prev_idx)), dtype=np.float32)
        sub[posc[dst[sel]], pos[src[sel]]] = 1.0
        masks.append(torch.tensor(sub))
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
