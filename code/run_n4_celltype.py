"""N4 cell-type-preserving null, whole brain. Edges are grouped by (cell_type(pre), cell_type(post))
using ANN-001; unannotated neurons form group NONE. Within each group edge endpoints are swapped
(degree-preserving, dp_rewire_c), so per-neuron in/out degree AND the cell-type-pair edge counts are
preserved. Singleton groups are fixed (reported). Writes results/stage_a/n4_results.json."""
import json, os, sys, time, gc
import numpy as np, pandas as pd, polars as pl, ctypes, scipy.sparse as sp
sys.path.insert(0, os.path.dirname(__file__))
import fast_census
ROOT = os.path.join(os.path.dirname(__file__), "..")
OUTA = os.path.join(ROOT, "results", "stage_a")
LIB = ctypes.CDLL(os.path.join(ROOT, "code", "dp_rewire_c.so"))
LIB.dp_rewire_c.restype = ctypes.c_longlong
LIB.dp_rewire_c.argtypes = [ctypes.c_void_p]*2 + [ctypes.c_longlong]*3 + [ctypes.c_uint64]
CL = ['003','012','102','021D','021U','021C','111D','111U','030T','030C','201','120D','120U','120C','210','300']
N_NULL = int(sys.argv[1]) if len(sys.argv) > 1 else 20
SWAPS, MASTER = 10, 29
ANN = sys.argv[2] if len(sys.argv) > 2 else "/tmp/ann.tsv"
t0 = time.time()
e = pl.read_parquet(os.path.join(OUTA, "edges_ge5.parquet"))
pre_r = e["pre_pt_root_id"].to_numpy(); post_r = e["post_pt_root_id"].to_numpy(); del e
nodes = np.unique(np.concatenate([pre_r, post_r])); nn = len(nodes)
a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type"]).drop_duplicates("root_id")
m = dict(zip(a.root_id, a.cell_type.fillna("NONE")))
tp = np.array([m.get(int(x), "NONE") for x in nodes])
ann_frac = float((tp != "NONE").mean())
codes = pd.factorize(tp)[0].astype(np.int64)
idx = np.searchsorted(nodes, pre_r), np.searchsorted(nodes, post_r)
src, dst = idx[0].astype(np.int64), idx[1].astype(np.int64)
key = codes[src] * (codes.max() + 1) + codes[dst]
order = np.argsort(key, kind="stable"); ks = key[order]
bounds = np.flatnonzero(np.diff(ks)) + 1
groups = [g for g in np.split(order, bounds) if len(g) >= 2]
n_single = int(len(src) - sum(len(g) for g in groups))
print(f"{nn} nodes {len(src)} edges, annotated frac {ann_frac:.4f}, {len(groups)} rewirable groups, {n_single} fixed edges [{time.time()-t0:.0f}s]", flush=True)
rng = np.random.SeedSequence(MASTER)
seeds = [int(x.generate_state(1)[0]) for x in rng.spawn(N_NULL)]
counts = []
for i in range(N_NULL):
    ti = time.time()
    r = np.random.default_rng(seeds[i]); gseeds = r.integers(1, 2**62, size=len(groups))
    p, q = src.copy(), dst.copy()
    for g, gs in zip(groups, gseeds):
        p2 = src[g].copy(); q2 = dst[g].copy()
        LIB.dp_rewire_c(p2.ctypes.data, q2.ctypes.data, len(g), nn, SWAPS * len(g), int(gs))
        p[g], q[g] = p2, q2
    A = sp.csr_matrix((np.ones(len(p), dtype=np.int64), (p, q)), shape=(nn, nn))
    A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros()
    c = fast_census.census(A); counts.append([c[k] for k in CL]); del A, p, q; gc.collect()
    print(f"null {i+1}/{N_NULL} [{time.time()-ti:.0f}s cum {time.time()-t0:.0f}s]", flush=True)
    json.dump({"counts": counts}, open("/tmp/n4_ckpt.json", "w"))
counts = np.array(counts, float)
obs = json.load(open(os.path.join(OUTA, "stage_a_analysis.json")))["observed"]
ob = np.array([obs[k] for k in CL], float); mean = counts.mean(0); sd = counts.std(0, ddof=1)
z = np.where(sd > 0, (ob - mean) / sd, np.sign(ob - mean) * 1e6)
emp = ((np.abs(counts - mean) >= np.abs(ob - mean)).sum(0) + 1) / (len(counts) + 1)
res = {"family": "N4 cell-type-pair-preserving (ANN-001 cell_type)", "n_null": N_NULL, "swaps_per_edge": SWAPS,
       "master_seed": MASTER, "engine": "dp_rewire_c", "annotated_node_fraction": ann_frac,
       "n_groups": len(groups), "fixed_edges": n_single, "n_edges": int(len(src)),
       "per_class": {CL[j]: {"observed": float(ob[j]), "null_mean": float(mean[j]), "null_sd": float(sd[j]),
                              "z": float(z[j]), "emp_p": float(emp[j])} for j in range(16)},
       "elapsed_s": time.time() - t0}
json.dump(res, open(os.path.join(OUTA, "n4_results.json"), "w"), indent=1)
print("DONE", flush=True)
