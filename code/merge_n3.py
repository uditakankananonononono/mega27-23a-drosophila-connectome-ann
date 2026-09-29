"""Merge N3 worker parts into results/stage_a/n3_results.json (z, emp_p, BH q over 16 classes)."""
import json, os
import numpy as np

OUTA = os.path.join(os.path.dirname(__file__), "..", "results", "stage_a")
CL = ['003','012','102','021D','021U','021C','111D','111U','030T','030C','201','120D','120U','120C','210','300']

def main():
    parts = [json.load(open(os.path.join(OUTA, f"n3_part_w{w}.json"))) for w in (0, 1)]
    counts, lo_hi = [], []
    for p in sorted(parts, key=lambda p: p["lo"]):
        counts.extend(p["counts"]); lo_hi.append((p["lo"], p["hi"]))
    assert lo_hi == [(0, 50), (50, 100)] and len(counts) == 100, (lo_hi, len(counts))
    counts = np.array(counts, dtype=np.float64)
    obs = json.load(open(os.path.join(OUTA, "stage_a_analysis.json")))["observed"]
    mean, sd = counts.mean(0), counts.std(0, ddof=1)
    ob = np.array([obs[k] for k in CL], dtype=np.float64)
    z = np.where(sd > 0, (ob - mean) / sd, np.sign(ob - mean) * 1e6)
    emp = ((np.abs(counts - mean) >= np.abs(ob - mean)).sum(0) + 1) / (len(counts) + 1)
    order = np.argsort(emp); q = np.empty(16); prev = 1.0
    for rank, j in enumerate(order[::-1]):
        val = min(prev, emp[j] * 16 / (16 - rank)); q[j] = val; prev = val
    res = {"family": "N3 compartment-preserving (endpoint primary neuropil, per-side)", "tier": 1,
           "n_null": 100, "swaps_per_edge": 10, "master_seed": 25,
           "engine": "dp_rewire_fast per compartment group (same N1 semantics as dp_rewire_np)",
           "workers": lo_hi,
           "classes": CL,
           "per_class": {CL[j]: {"observed": float(ob[j]), "null_mean": float(mean[j]), "null_sd": float(sd[j]),
                                  "z": float(z[j]), "emp_p": float(emp[j]), "bh_q": float(q[j])} for j in range(16)}}
    json.dump(res, open(os.path.join(OUTA, "n3_results.json"), "w"), indent=1)
    for c in CL:
        p = res["per_class"][c]
        print(f"{c}: z={p['z']:+.1f} q={p['bh_q']:.3f}")

if __name__ == "__main__":
    main()
