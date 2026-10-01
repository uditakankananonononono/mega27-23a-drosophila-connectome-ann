"""A30: fly mask as prior vs magnitude pruning, same pipeline. H30a fly_dwft>rand_dwft, H30b hyb_half>prune_mag_lw, H30c fly_dwft>prune_mag_lw.
Paired exact Wilcoxon by seed_idx per condition, Holm over 3."""
import json, glob, numpy as np
from scipy.stats import wilcoxon
ARMS = ("fly_dwft", "hyb_half", "rand_dwft", "prune_mag_lw", "fly_m_c")
FR = ["0.0", "0.1", "0.2", "0.3", "0.4", "0.5"]; X = [float(f) for f in FR]
D = {}
for f in glob.glob("results/stage_c/runs/*.json"):
    d = json.load(open(f))
    if d["arm"] not in ARMS: continue
    if d["arm"] == "fly_m_c" and "|abl|" in d["run_id"]:
        D[(d["arm"], d["task"], 0.0, int(d["run_id"].split("|k")[1]), True)] = d; continue
    k = int(d["run_id"].split("|k")[1])
    D[(d["arm"], d["task"], d["sigma"], k, False)] = d
    if d.get("ablation"): D[(d["arm"], d["task"], d["sigma"], k, True)] = d
conds = [("T1_mnist_noise", 0.0), ("T1_mnist_noise", 1.0), ("T2_fashion", 0.0), ("T4_permuted_mnist", 0.0), ("T5_cifar10_subset", 0.0)]
def acc(a, t, s): return np.array([D[(a, t, s, k, False)]["epochs"][-1]["val_acc"] for k in range(20)])
def ret(a, t):
    x = np.array([[D[(a, t, 0.0, k, True)]["ablation"][fr] for fr in FR] for k in range(20)]); return x, x / x[:, [0]]
def holm(ps):
    o = sorted(ps, key=ps.get); m = len(o); prev = 0; out = {}
    for i, r in enumerate(o): prev = min(1.0, max(prev, (m - i) * ps[r])); out[r] = prev
    return out
out = {"primary": {}, "means": {}, "robustness": {}, "layer_nnz_sample": {}, "chance_flags": {}}
tests = {"H30a_fly_dwft_vs_rand_dwft": ("fly_dwft", "rand_dwft"), "H30b_hyb_half_vs_prune_mag_lw": ("hyb_half", "prune_mag_lw"), "H30c_fly_dwft_vs_prune_mag_lw": ("fly_dwft", "prune_mag_lw")}
for t, s in conds:
    key = f"{t}|s{s}"; out["means"][key] = {a: round(float(acc(a, t, s).mean()), 4) for a in ARMS if (a, t, s, 0, False) in D}
    ps = {}; res = {}
    for name, (a, b) in tests.items():
        xa, xb = acc(a, t, s), acc(b, t, s); p = float(wilcoxon(xa, xb).pvalue); ps[name] = p
        res[name] = {"a_mean": round(float(xa.mean()), 4), "b_mean": round(float(xb.mean()), 4), "wins_a": int((xa > xb).sum()), "p": p}
    for n, v in holm(ps).items(): res[n]["p_holm"] = v
    out["primary"][key] = res
for t in ["T1_mnist_noise", "T4_permuted_mnist"]:
    R = {a: ret(a, t) for a in ("fly_dwft", "hyb_half", "rand_dwft", "prune_mag_lw", "fly_m_c")}
    A = {a: np.trapezoid(r[1], X, axis=1) for a, r in R.items()}
    res = {"auc_x2": {a: round(float(2 * v.mean()), 4) for a, v in A.items()}, "ret40": {a: round(float(r[1][:, 4].mean()), 4) for a, r in R.items()},
           "abs_acc0": {a: round(float(r[0][:, 0].mean()), 4) for a, r in R.items()}, "abs_acc40": {a: round(float(r[0][:, 4].mean()), 4) for a, r in R.items()}, "vs_prune_mag_lw": {}}
    for a in ("fly_dwft", "hyb_half", "rand_dwft"):
        res["vs_prune_mag_lw"][a] = {"wins": int((A[a] > A["prune_mag_lw"]).sum()), "p": float(wilcoxon(A[a], A["prune_mag_lw"]).pvalue)}
    out["robustness"][t] = res
for a in ("fly_dwft", "hyb_half", "rand_dwft"):
    out["layer_nnz_sample"][a] = {f"{t}": D[(a, t, s, 0, False)]["layer_nnz"] for t, s in conds[:1] + conds[2:]}
json.dump(out, open("results/stage_c/collected/a30.json", "w"), indent=1)
for k, v in out["means"].items(): print(k, v)
for k, v in out["primary"].items():
    print(k)
    for n, r in v.items(): print("  ", n, r)
for k, v in out["robustness"].items(): print(k, json.dumps(v))
print(out["layer_nnz_sample"])
