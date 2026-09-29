"""AMENDMENT-6 escalation: DP chains to 40 swaps/edge, 3 seeded chains (23/24/25).
Censuses at 0/1/2/5/10/20/40 E. Plateau test on the 20E->40E window per chain.
Writes results/stage_a/convergence_40e.json."""
import json, os, sys, time
import numpy as np
import polars as pl
sys.path.insert(0, os.path.dirname(__file__))
import nulls, nulls_convergence

OUTA = os.path.join(os.path.dirname(__file__), "..", "results", "stage_a")
FR = (0, 1, 2, 5, 10, 20, 40)

def main():
    t0 = time.time()
    edges = pl.read_parquet(os.path.join(OUTA, "edges_ge5.parquet"))
    nodes = np.unique(pl.concat([edges["pre_pt_root_id"], edges["post_pt_root_id"]]).unique().to_numpy())
    idx = {r: i for i, r in enumerate(nodes)}
    src = np.fromiter((idx[r] for r in edges["pre_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    dst = np.fromiter((idx[r] for r in edges["post_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    print(f"graph {len(nodes)} nodes {len(src)} edges [{time.time()-t0:.0f}s]", flush=True)
    chains = {}
    for seed in (23, 24, 25):
        ts = time.time()
        out = nulls_convergence.run_chain(src, dst, len(nodes), seed=seed, fractions=FR)
        chains[str(seed)] = {str(k): v for k, v in out.items()}
        # plateau on 20E->40E
        a, b = out[20], out[40]
        rows, ok = {}, True
        for k in a:
            if b[k] >= 100:
                rel = abs(b[k]-a[k])/max(abs(b[k]),1)
                rows[k] = rel
                if rel >= 0.02: ok = False
        chains[str(seed)]['plateau_20E_40E'] = rows
        chains[str(seed)]['converged_20E_40E'] = bool(ok)
        print(f"chain seed={seed} converged={ok} [{time.time()-ts:.0f}s] " +
              str({k: round(v,4) for k,v in rows.items() if v >= 0.02}), flush=True)
    res = {"amendment": "A26 (AMENDMENT-6)", "seeds": [23,24,25],
           "fractions_E_swaps": list(FR), "chains": chains,
           "criterion": "|count(40E)-count(20E)|/|count(40E)| < 0.02 for classes with count(40E)>=100, all chains",
           "elapsed_s": time.time()-t0}
    json.dump(res, open(os.path.join(OUTA, "convergence_40e.json"), "w"), indent=1)
    print(f"DONE [{time.time()-t0:.0f}s]", flush=True)

if __name__ == "__main__":
    main()
