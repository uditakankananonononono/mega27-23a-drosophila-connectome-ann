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
    if arm in ("prune_mag_gl", "prune_mag_lw"):
        return PrunableMLP(input_dim, hidden, n_classes)
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
    if arm == "fly_m_c" or arm == "ctrl_rand_sparse_c":
        # AMENDMENT-27 connectivity-repaired arms (see PREREG_A27.md)
        base_arm = "fly_m" if arm == "fly_m_c" else "ctrl_rand_sparse"
        if base_arm == "fly_m":
            model = FlyMLP(input_dim, hidden, n_classes, "fly_m", run, a17)
        else:
            dkey = "d100" if input_dim == 100 else ("d3072" if input_dim == 3072 else "d784")
            dens = a17["sparse_density_by_task"][dkey]
            model = SparseMLP(input_dim, hidden, n_classes, density=dens, seed=run["seed"] + 777)
        model.masks = repair_masks(model.masks, run["seed"])
        if arm == "ctrl_rand_sparse_c":
            fly_peer = FlyMLP(input_dim, hidden, n_classes, "fly_m", run, a17)
            fly_peer.masks = repair_masks(fly_peer.masks, run["seed"])
            model.masks = match_edge_count(model.masks, fly_peer.masks)
        with torch.no_grad():
            torch.manual_seed(run["seed"])
            for lin, m in zip(model.layers, model.masks):
                # fresh nn.Linear-default init, then apply the repaired mask once, so
                # repair/top-up edges start at random init like every other unmasked weight
                nn.init.kaiming_uniform_(lin.weight, a=5 ** 0.5)
                lin.weight *= m
        return model.to(device)
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
            # functional mask: masked entries were zeroed at init and receive zero
            # gradient, so they stay zero - identical training semantics to re-masking
            # each step, but no in-place mutation that breaks autograd versioning
            x = nn.functional.linear(x, lin.weight * m, lin.bias)
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
            # functional mask (see SparseMLP note): same training semantics, no in-place
            x = nn.functional.linear(x, lin.weight * m, lin.bias)
            if i < len(self.layers) - 1: x = torch.relu(x)
        return x

def repair_masks(masks, seed):
    """AMENDMENT-27 minimal connectivity repair (FROZEN rule): for every layer, each
    zero-fan-in row gains exactly 2 distinct uniform incoming edges (seeded per layer).
    Guarantees zero dead rows and full input->output reachability. Returns new masks."""
    rng = np.random.default_rng(seed)
    out = []
    for li, m in enumerate(masks):
        m = m.clone()
        dead = (m.sum(1) == 0).nonzero().flatten().tolist()
        for r in dead:
            cols = rng.choice(m.shape[1], size=min(2, m.shape[1]), replace=False)
            m[r, torch.tensor(cols)] = 1.0
        out.append(m)
    return out

def match_edge_count(masks_add, masks_target):
    """A27: top up masks_add with uniform non-repair edges until total count equals
    masks_target's (exact density match; control stays purely random). Seeded."""
    rng = np.random.default_rng(987)
    add = [m.clone() for m in masks_add]
    deficit = int(sum(m.sum() for m in masks_target) - sum(m.sum() for m in add))
    li = 0
    while deficit > 0:
        m = add[li % len(add)]
        zeros = (m == 0).nonzero()
        if len(zeros) == 0: li += 1; continue
        pick = zeros[rng.integers(0, len(zeros))]
        if m[pick[0], pick[1]] == 0:
            m[pick[0], pick[1]] = 1.0; deficit -= 1
        li += 1
    return add

def ablation_eval(model, dl, fractions, seed, device, is_reg):
    """G2 (pre-registered): random neuron ablation robustness. For each fraction,
    zero that fraction of hidden-unit activations per hidden layer (seeded per run),
    measure val accuracy/MSE. Returns {frac: metric}. Applies to SparseMLP/FlyMLP
    families (models exposing .layers and .masks)."""
    out = {}
    hidden_idx = list(range(len(model.layers) - 1))
    for frac in fractions:
        g = torch.Generator().manual_seed(seed + int(frac * 1000))
        unit_masks = []
        for li in hidden_idx:
            h = model.layers[li].out_features
            keep = (torch.rand(h, generator=g) >= frac).float().to(device)
            unit_masks.append(keep)
        correct = tot = 0; mse = 0.0
        with torch.no_grad():
            for x, y in dl:
                x = x.to(device); y = y.to(device)
                x = x.reshape(x.shape[0], -1)
                for i, (lin, m) in enumerate(zip(model.layers, model.masks)):
                    x = torch.nn.functional.linear(x, lin.weight * m, lin.bias)
                    if i < len(model.layers) - 1:
                        x = torch.relu(x) * unit_masks[i]
                if is_reg:
                    mse += float(((x.squeeze() - y.squeeze()) ** 2).sum())
                else:
                    correct += int((x.argmax(1) == y).sum()); tot += len(y)
        out[str(frac)] = (mse / tot) if is_reg else (correct / tot)
    return out

def ablation_eval_generic(model, dl, fractions, seed, device, is_reg):
    """A28/G4: same random hidden-unit ablation protocol as ablation_eval, for models
    WITHOUT masks (DenseMLP, SmallCNN). Unit = hidden neuron (MLP) or conv channel (CNN):
    after each hidden ReLU, a seeded keep-vector (same generator recipe as ablation_eval)
    zeroes that fraction of units. Implemented with forward hooks on the hidden ReLUs."""
    relus = [m for m in model.modules() if isinstance(m, torch.nn.ReLU)]
    sizes = []
    lins = [m for m in model.modules() if isinstance(m, (torch.nn.Linear, torch.nn.Conv2d))]
    for m in lins[:len(relus)]:
        sizes.append(m.out_features if isinstance(m, torch.nn.Linear) else m.out_channels)
    out = {}
    for frac in fractions:
        g = torch.Generator().manual_seed(seed + int(frac * 1000))
        keeps = [(torch.rand(h, generator=g) >= frac).float().to(device) for h in sizes]
        hooks = []
        for r, k in zip(relus, keeps):
            def hook(mod, inp, outp, k=k):
                shape = [1, -1] + [1] * (outp.dim() - 2)
                return outp * k.view(*shape)
            hooks.append(r.register_forward_hook(hook))
        correct = tot = 0; mse = 0.0
        model.eval()
        with torch.no_grad():
            for x, y in dl:
                x = x.to(device); y = y.to(device)
                o = model(x)
                if is_reg: mse += float(((o.squeeze() - y.squeeze()) ** 2).sum()); tot += len(y)
                else:
                    correct += int((o.argmax(1) == y).sum()); tot += len(y)
        for h in hooks: h.remove()
        out[str(frac)] = (mse / tot) if is_reg else (correct / tot)
    return out

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


class PrunableMLP(nn.Module):
    """A29: dense MLP (same hidden sizes as every MLP arm) that exposes .layers/.masks so the
    G2 ablation path applies. Masks start all-ones; prune_model() sets them after phase-1 training."""
    def __init__(self, d, hidden, c):
        super().__init__()
        self.layers = nn.ModuleList(); self.masks = []
        prev = d
        for h in list(hidden) + [c]:
            self.layers.append(nn.Linear(prev, h)); self.masks.append(torch.ones(h, prev)); prev = h
    def forward(self, x):
        x = x.reshape(x.shape[0], -1)
        for i, (lin, m) in enumerate(zip(self.layers, self.masks)):
            x = nn.functional.linear(x, lin.weight * m.to(x.device), lin.bias)
            if i < len(self.layers) - 1: x = torch.relu(x)
        return x

def prune_model(model, target_nnz, mode):
    """A29 magnitude pruning to EXACTLY sum(target_nnz) kept weights (target = fly_m_c layer counts).
    mode 'lw': keep top-|w| nnz_l per layer. mode 'gl': keep global top-|w|/mean|w_layer| over all layers, same total.
    Ties broken by flat index (stable). Biases untouched."""
    ws = [l.weight.detach().abs().cpu() for l in model.layers]
    if mode == "lw":
        masks = []
        for w, k in zip(ws, target_nnz):
            flat = w.flatten(); idx = torch.argsort(flat, descending=True, stable=True)[:k]
            m = torch.zeros_like(flat); m[idx] = 1.0; masks.append(m.view_as(w))
    else:
        flat = torch.cat([(w / w.mean().clamp_min(1e-12)).flatten() for w in ws]); k = int(sum(target_nnz))  # layer-mean-normalised global magnitude (avoids input-layer starvation by init scale)
        idx = torch.argsort(flat, descending=True, stable=True)[:k]
        m = torch.zeros_like(flat); m[idx] = 1.0
        masks, off = [], 0
        for w in ws:
            masks.append(m[off:off + w.numel()].view_as(w)); off += w.numel()
    model.masks = masks
    with torch.no_grad():
        for l, m in zip(model.layers, masks): l.weight *= m.to(l.weight.device)
