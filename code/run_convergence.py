"""Driver: null convergence diagnostic (AMENDMENT-4 A13) on the whole-brain graph.
Continues one DP chain to 20 swaps/edge, censusing at 0,1,2,5,10,20 E swaps.
Writes results/stage_a/convergence.json."""
import json, os, sys, time
import numpy as np
import polars as pl
sys.path.insert(0, os.path.dirname(__file__))
import nulls_convergence

OUTA = os.path.join(os.path.dirname(__file__), "..", "results", "stage_a")

def main():
    t0 = time.time()
    edges = pl.read_parquet(os.path.join(OUTA, "edges_ge5.parquet"))
    nodes = np.unique(pl.concat([edges["pre_pt_root_id"], edges["post_pt_root_id"]]).unique().to_numpy())
    idx = {r: i for i, r in enumerate(nodes)}
    src = np.fromiter((idx[r] for r in edges["pre_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    dst = np.fromiter((idx[r] for r in edges["post_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    print(f"graph {len(nodes)} nodes {len(src)} edges [{time.time()-t0:.0f}s]", flush=True)
    out = nulls_convergence.run_chain(src, dst, len(nodes), seed=23)
    rows, ok = nulls_convergence.plateau_report(out)
    res = {"seed": 23, "fractions_E_swaps": [0, 1, 2, 5, 10, 20],
           "census": {str(k): v for k, v in out.items()},
           "plateau_rel_change_10E_to_20E": rows, "converged": bool(ok),
           "criterion": "|count(20E)-count(10E)|/|count(20E)| < 0.02 for classes with count(20E)>=100",
           "elapsed_s": time.time() - t0}
    json.dump(res, open(os.path.join(OUTA, "convergence.json"), "w"), indent=1)
    print("converged:", ok, flush=True)
    print("per-class rel change:", {k: (round(v, 5) if v is not None else None) for k, v in rows.items()}, flush=True)
    print(f"DONE [{time.time()-t0:.0f}s]", flush=True)

if __name__ == "__main__":
    main()
