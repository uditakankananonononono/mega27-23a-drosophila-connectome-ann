"""A29: fly_m_c vs magnitude-pruned dense (lw, gl) at identical nonzero-weight budget. Paired exact Wilcoxon by seed_idx, Holm over 2 refs."""
import json, glob, collections, numpy as np
from scipy.stats import wilcoxon
FR = ["0.0", "0.1", "0.2", "0.3", "0.4", "0.5"]; X = [float(f) for f in FR]
D = {}
for f in glob.glob("results/stage_c/runs/*.json"):
    d = json.load(open(f))
    if d["arm"] not in ("fly_m_c", "prune_mag_gl", "prune_mag_lw", "ctrl_rand_sparse_c"): continue
    abl = ("|abl|" in d["run_id"]) and not d["arm"].startswith("prune_mag")
    if d["arm"].startswith("prune_mag"): D[(d["arm"], d["task"], d["sigma"], int(d["run_id"].split("|k")[1]), True)] = d
    D[(d["arm"], d["task"], d["sigma"], int(d["run_id"].split("|k")[1]), abl)] = d
def acc(arm, t, s):
    return np.array([D[(arm, t, s, k, False)]["epochs"][-1]["val_acc"] for k in range(20)])
def ret(arm, t):
    a = np.array([[D[(arm, t, 0.0, k, True)]["ablation"][fr] for fr in FR] for k in range(20)])
    return a / a[:, [0]]
def holm(ps):
    o = sorted(ps, key=ps.get); m = len(o); prev = 0; out = {}
    for i, r in enumerate(o):
        prev = min(1.0, max(prev, (m - i) * ps[r])); out[r] = prev
    return out
out = {"H29a": {}, "H29b": {}, "layer_nnz": {}, "efficiency": {}}
conds = [("T1_mnist_noise", 0.0), ("T1_mnist_noise", 1.0), ("T2_fashion", 0.0), ("T4_permuted_mnist", 0.0), ("T5_cifar10_subset", 0.0)]
refs = ["prune_mag_gl", "prune_mag_lw"]
for t, s in conds:
    fa = acc("fly_m_c", t, s); res = {"fly_m_c_mean": round(float(fa.mean()), 4), "ctrl_rand_sparse_c_mean": round(float(acc("ctrl_rand_sparse_c", t, s).mean()), 4)}
    ps = {}
    for r in refs:
        ra = acc(r, t, s); p = float(wilcoxon(fa, ra).pvalue)
        res[r] = {"mean": round(float(ra.mean()), 4), "wins_fly": int((fa > ra).sum()), "p": p}; ps[r] = p
    for r, v in holm(ps).items(): res[r]["p_holm"] = v
    out["H29a"][f"{t}|s{s}"] = res
for t in ["T1_mnist_noise", "T4_permuted_mnist"]:
    R = {a: ret(a, t) for a in ["fly_m_c", "ctrl_rand_sparse_c"] + refs}
    A = {a: np.trapezoid(r, X, axis=1) for a, r in R.items()}
    res = {"auc_norm_x2": {a: round(float(2 * v.mean()), 4) for a, v in A.items()}, "ret40": {a: round(float(r[:, 4].mean()), 4) for a, r in R.items()}, "abs_acc_at_0": {}}
    for a in R: res["abs_acc_at_0"][a] = round(float(np.mean([D[(a, t, 0.0, k, True)]["ablation"]["0.0"] for k in range(20)])), 4)
    ps = {}
    for r in refs:
        p = float(wilcoxon(A["fly_m_c"], A[r]).pvalue); ps[r] = p
        res[r] = {"wins_fly": int((A["fly_m_c"] > A[r]).sum()), "p": p}
    for r, v in holm(ps).items(): res[r]["p_holm"] = v
    out["H29b"][t] = res
for a in refs + ["fly_m_c"]:
    if a in refs: out["layer_nnz"][a] = {t: sorted({tuple(D[(a, t, s, k, False)]["layer_nnz"]) for k in range(20)}) for t, s in conds[:1] + conds[2:]}
    out["efficiency"][a] = {f"{t}|s{s}": {"acc": round(float(acc(a, t, s).mean()), 4), "eff_params": int(D[(a, t, s, 0, False)]["n_params_effective"]), "eff_flops": int(D[(a, t, s, 0, False)]["flops_effective"])} for t, s in conds}
json.dump(out, open("results/stage_c/collected/a29.json", "w"), indent=1)
for k, v in out["H29a"].items(): print(k, json.dumps(v))
for k, v in out["H29b"].items(): print(k, json.dumps(v))
print(json.dumps(out["layer_nnz"]))
