"""F: efficiency ratio = acc_final / FLOPs_effective (MFLOP); learning speed = mean val_acc over epochs (learning-curve AUC) and epochs to reach 90% of own final acc. Sigma=0 runs, no ablation rows. Descriptive, 20 seeds, paired Wilcoxon fly_m_c vs ctrl_rand_sparse_c on learning-curve AUC."""
import json, glob, numpy as np
from collections import defaultdict
from scipy.stats import wilcoxon
R = defaultdict(dict)
for f in glob.glob("results/stage_c/runs/*.json"):
    d = json.load(open(f))
    if d["sigma"] != 0.0 or "|abl|" in d["run_id"] or not d.get("epochs"): continue
    d["epochs"] = [e for e in d["epochs"] if "val_acc" in e]
    if not d["epochs"]: continue
    R[(d["arm"], d["task"])][d["run_id"]] = d
out = {}
for (a, t), runs in sorted(R.items()):
    acc = [r["epochs"][-1]["val_acc"] for r in runs.values()]
    fl = [(r.get("flops_effective") or r["flops"]) for r in runs.values()]
    auc = [np.mean([e["val_acc"] for e in r["epochs"]]) for r in runs.values()]
    t90 = [next(e["epoch"] for e in r["epochs"] if e["val_acc"] >= .9 * r["epochs"][-1]["val_acc"]) for r in runs.values()]
    out[f"{a}|{t}"] = {"n": len(runs), "acc": round(float(np.mean(acc)), 4), "flops_eff": int(np.mean(fl)), "acc_per_MFLOP": round(float(np.mean(acc) / (np.mean(fl) / 1e6)), 3), "curve_auc": round(float(np.mean(auc)), 4), "epochs_to_90pct_final": round(float(np.mean(t90)), 2)}
def paired(a, b, t):
    ka = {k.rsplit("|k", 1)[1]: np.mean([e["val_acc"] for e in r["epochs"]]) for k, r in R[(a, t)].items()}
    kb = {k.rsplit("|k", 1)[1]: np.mean([e["val_acc"] for e in r["epochs"]]) for k, r in R[(b, t)].items()}
    ks = sorted(set(ka) & set(kb)); x = np.array([ka[k] for k in ks]); y = np.array([kb[k] for k in ks])
    return {"n": len(ks), "wins": int((x > y).sum()), "p": float(wilcoxon(x, y).pvalue)}
out["paired_curve_auc_fly_vs_rand"] = {t: paired("fly_m_c", "ctrl_rand_sparse_c", t) for t in sorted({t for _, t in R}) if ("fly_m_c", t) in R and ("ctrl_rand_sparse_c", t) in R}
json.dump(out, open("results/stage_c/collected/flops_speed.json", "w"), indent=1)
for k, v in out.items(): print(k, v)
