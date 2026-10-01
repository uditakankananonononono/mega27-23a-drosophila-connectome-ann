"""A28/G4: ablation retention of fly_m_c vs base_dense, small_cnn, base_sparse (and ctrl_rand_sparse_c, descriptive).
Retention = acc(frac)/acc(0) per run; retention-AUC trapezoid over 0-0.5. Paired exact Wilcoxon by seed_idx; Holm over 3 refs per task."""
import json, glob, os, numpy as np
from scipy.stats import wilcoxon
FR = ["0.0", "0.1", "0.2", "0.3", "0.4", "0.5"]; X = [float(f) for f in FR]
R = {}
for f in glob.glob("results/stage_c/runs/*|abl|*.json"):
    d = json.load(open(f)); k = int(d["run_id"].split("|k")[1])
    R[(d["arm"], d["task"], k)] = d["ablation"]
def curves(arm, task):
    a = np.array([[R[(arm, task, k)][fr] for fr in FR] for k in range(20)])
    return a
out = {"metric": "retention acc(frac)/acc(0); retention-AUC trapezoid 0-0.5", "tasks": {}}
for task in ["T1_mnist_noise", "T4_permuted_mnist"]:
    cur = {a: curves(a, task) for a in ["fly_m_c", "ctrl_rand_sparse_c", "base_dense", "small_cnn", "base_sparse"]}
    ret = {a: c / c[:, [0]] for a, c in cur.items()}
    auc = {a: np.trapezoid(r, X, axis=1) for a, r in ret.items()}
    t = {"abs_acc_at_0": {a: round(float(c[:, 0].mean()), 4) for a, c in cur.items()},
         "retention_auc_mean": {a: round(float(v.mean()), 4) for a, v in auc.items()},
         "retention_by_frac": {a: [round(float(x), 4) for x in r.mean(0)] for a, r in ret.items()},
         "abs_acc_by_frac": {a: [round(float(x), 4) for x in c.mean(0)] for a, c in cur.items()}, "tests": {}}
    ps = {}
    for ref in ["base_dense", "small_cnn", "base_sparse", "ctrl_rand_sparse_c"]:
        d = auc["fly_m_c"] - auc[ref]
        p = float(wilcoxon(auc["fly_m_c"], auc[ref]).pvalue)
        d4 = ret["fly_m_c"][:, 4] - ret[ref][:, 4]; p4 = float(wilcoxon(ret["fly_m_c"][:, 4], ret[ref][:, 4]).pvalue)
        t["tests"][ref] = {"auc_fly": round(float(auc["fly_m_c"].mean()), 4), "auc_ref": round(float(auc[ref].mean()), 4),
                           "wins_fly": int((d > 0).sum()), "p": p, "ret40_fly": round(float(ret["fly_m_c"][:, 4].mean()), 4),
                           "ret40_ref": round(float(ret[ref][:, 4].mean()), 4), "wins_fly_ret40": int((d4 > 0).sum()), "p_ret40": p4}
        if ref != "ctrl_rand_sparse_c": ps[ref] = p
    order = sorted(ps, key=ps.get); m = len(order); prev = 0
    for i, r in enumerate(order):
        adj = min(1.0, max(prev, (m - i) * ps[r])); prev = adj; t["tests"][r]["p_holm"] = adj
    out["tasks"][task] = t
json.dump(out, open("results/stage_c/collected/g4_ablation.json", "w"), indent=1)
for task, t in out["tasks"].items():
    print(task, "abs0", t["abs_acc_at_0"]); print(" auc", t["retention_auc_mean"])
    for r, v in t["tests"].items(): print(" ", r, v)
