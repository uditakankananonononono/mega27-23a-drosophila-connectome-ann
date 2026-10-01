"""G3 analysis: dense and CNN reference arms vs sparse/fly arms (clean runs only, ablation is None)."""
import json, glob, os, collections, numpy as np
from scipy.stats import wilcoxon
runs = collections.defaultdict(list)
meta = {}
for f in glob.glob("results/stage_c/runs/*.json"):
    if os.path.basename(f).startswith("_"): continue
    d = json.load(open(f))
    if d.get("ablation") is not None or "|abl|" in d["run_id"]: continue
    acc = d["epochs"][-1]["val_acc"] if d["task"] != "T3_adding" else None
    key = (d["arm"], d["task"], d["sigma"])
    runs[key].append((d["seed"], d["run_id"], d["final"], d["epochs"][-1]))
    meta[d["arm"]] = (d["n_params"], d["n_params_effective"], d["flops"], d["flops_effective"])
def val(e):
    return e["val_acc"] if "val_acc" in e else -e.get("val_mse", np.nan)
def arr(arm, task, sig):
    r = sorted(runs.get((arm, task, sig), []), key=lambda x: x[1].split("|k")[-1])
    return np.array([val(x[3]) for x in r])
arms = sorted({k[0] for k in runs})
out = {"arms": arms, "n_by_arm": {a: sum(len(v) for k, v in runs.items() if k[0] == a) for a in arms},
       "params_flops": {a: dict(zip(["n_params", "n_params_eff", "flops", "flops_eff"], meta[a])) for a in arms},
       "mean_acc": {}, "t1_noise_auc": {}, "pairs": {}}
for (a, t, s) in sorted(runs):
    out["mean_acc"][f"{a}|{t}|s{s}"] = round(float(np.mean(arr(a, t, s))), 4)
sig = [0.0, 0.5, 1.0, 1.5]
def auc(a):
    m = [arr(a, "T1_mnist_noise", s) for s in sig]
    if any(len(x) == 0 for x in m): return None
    return np.trapz(np.array(m), sig, axis=0)
for a in arms:
    x = auc(a)
    if x is not None: out["t1_noise_auc"][a] = [round(float(x.mean()), 4), round(float(x.std()), 4)]
def cmp(a, b, label, fn):
    xa, xb = fn(a), fn(b)
    if xa is None or xb is None or len(xa) != len(xb) or len(xa) == 0: return
    d = xa - xb
    p = float(wilcoxon(xa, xb).pvalue) if np.any(d != 0) else 1.0
    out["pairs"][f"{a}_vs_{b}|{label}"] = {"a_mean": round(float(xa.mean()), 4), "b_mean": round(float(xb.mean()), 4),
                                             "wins_a": int((d > 0).sum()), "n": len(d), "p": p}
for ref in ["base_dense", "small_cnn"]:
    for arm in ["fly_m_c", "ctrl_rand_sparse_c", "base_sparse"]:
        cmp(ref, arm, "T1_noise_auc", auc)
        for t, s in [("T2_fashion", 0.0), ("T4_permuted_mnist", 0.0), ("T5_cifar10_subset", 0.0), ("T1_mnist_noise", 0.0)]:
            cmp(ref, arm, f"{t}|s{s}", lambda a, t=t, s=s: (arr(a, t, s) if len(arr(a, t, s)) else None))
json.dump(out, open("results/stage_c/collected/g3_refs.json", "w"), indent=1)
print(json.dumps({k: out[k] for k in ["n_by_arm", "params_flops", "t1_noise_auc"]}, indent=0))
for k, v in out["pairs"].items(): print(k, v)
