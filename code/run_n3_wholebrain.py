"""N3 compartment-preserving null, whole brain, Tier 1 (A1/A12/A14), 100 replicates.
Preserves per-neuron in/out degree AND each endpoint's primary neuropil
(pre-side primary for pre endpoint, post-side primary for post endpoint; n3_null.py semantics).
Per-side primaries: running argmax over streamed feather batches, filtered to graph nodes.
Groups precomputed ONCE (compartments are fixed across replicates); per-group rewire uses
dp_rewire_fast (same N1 semantics as dp_rewire_np; np engine is pathologically slow on small
groups). Singleton groups unrewirable (honest limitation, n3_null.py). 10 swaps/edge (matches N1).
Checkpoints every 10 nulls; resume-safe. Writes results/stage_a/n3_results.json."""
import json, os, sys, time, gc
import numpy as np
import polars as pl
from pyarrow import ipc as _ipc
sys.path.insert(0, os.path.dirname(__file__))
import nulls, nulls_convergence, fast_census
import scipy.sparse as sp
import ctypes as _ct
_LIB = _ct.CDLL(os.path.join(os.path.dirname(__file__), "dp_rewire_c.so"))
_LIB.dp_rewire_c.restype = _ct.c_longlong
_LIB.dp_rewire_c.argtypes = [_ct.c_void_p, _ct.c_void_p, _ct.c_longlong, _ct.c_longlong, _ct.c_longlong, _ct.c_uint64]
def _c_rewire(pre, post, n, swaps, seed):
    p = pre.astype(np.int64).copy(); q = post.astype(np.int64).copy()
    acc = _LIB.dp_rewire_c(p.ctypes.data, q.ctypes.data, len(p), n, swaps, seed)
    if acc < swaps: print(f"WARN stall: {acc}/{swaps}", flush=True)
    return p, q

OUTA = os.path.join(os.path.dirname(__file__), "..", "results", "stage_a")
RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
MASTER_SEED = 25  # N3 family seed (23=Stage A, 24=Stage B)
N_NULL, SWAPS = 100, 10
# two-worker split (2 CPU box, checkpoint-resume safe): worker w covers [w*50,(w+1)*50)
import sys as _s
W = int(_s.argv[1]) if len(_s.argv) > 1 else 0
NW = int(_s.argv[2]) if len(_s.argv) > 2 else 1
SPAN = N_NULL // NW
LO, HI = W * SPAN, (W + 1) * SPAN
CKPT = os.path.join(OUTA, f"n3_checkpoint_w{W}.json")

def side_primary(path, idcol, keep):
    keep = set(int(r) for r in keep)
    best = {}
    r = _ipc.open_file(path)
    for bi in range(r.num_record_batches):
        f = pl.from_arrow(r.get_batch(bi))
        for rid, npil, c in zip(f[idcol].to_numpy(), f["neuropil"].to_numpy(), f["count"].to_numpy()):
            rid = int(rid)
            if rid not in keep: continue
            cur = best.get(rid)
            if cur is None or c > cur[1] or (c == cur[1] and npil < cur[0]):
                best[rid] = (npil, int(c))
    return {k: v[0] for k, v in best.items()}

def main():
    t0 = time.time()
    edges = pl.read_parquet(os.path.join(OUTA, "edges_ge5.parquet"))
    nodes = np.unique(pl.concat([edges["pre_pt_root_id"], edges["post_pt_root_id"]]).unique().to_numpy())
    pre_roots = edges["pre_pt_root_id"].to_numpy(); post_roots = edges["post_pt_root_id"].to_numpy()
    print(f"graph {len(nodes)} nodes {edges.height} edges [{time.time()-t0:.0f}s]", flush=True)
    pre_prim = side_primary(os.path.join(RAW, "per_neuron_neuropil_count_pre_783.feather"), "pre_pt_root_id", nodes)
    print(f"pre primaries {len(pre_prim)} [{time.time()-t0:.0f}s]", flush=True)
    post_prim = side_primary(os.path.join(RAW, "per_neuron_neuropil_count_post_783.feather"), "post_pt_root_id", nodes)
    print(f"post primaries {len(post_prim)} [{time.time()-t0:.0f}s]", flush=True)
    del edges; gc.collect()
    comp = {}
    for i in range(len(pre_roots)):
        key = (pre_prim.get(int(pre_roots[i]), "NONE"), post_prim.get(int(post_roots[i]), "NONE"))
        comp.setdefault(key, []).append(i)
    groups = [np.array(v, dtype=np.int64) for k, v in sorted(comp.items()) if len(v) >= 2]
    n_single = sum(len(v) for v in comp.values() if len(v) < 2)
    del comp; gc.collect()
    print(f"{len(groups)} rewirable groups, {n_single} singleton-group edges fixed [{time.time()-t0:.0f}s]", flush=True)
    idx = {r: i for i, r in enumerate(nodes)}
    src_all = np.fromiter((idx[int(r)] for r in pre_roots), dtype=np.int64, count=len(pre_roots))
    dst_all = np.fromiter((idx[int(r)] for r in post_roots), dtype=np.int64, count=len(post_roots))
    del pre_roots, post_roots; gc.collect()
    n_nodes = len(nodes)
    CL = ['003','012','102','021D','021U','021C','111D','111U','030T','030C','201','120D','120U','120C','210','300']
    done_counts = []
    start_i = LO
    if os.path.exists(CKPT):
        ck = json.load(open(CKPT))
        if ck.get("params") == [N_NULL, SWAPS, MASTER_SEED, W]:
            done_counts, start_i = ck["counts"], ck["n_done"]
            print(f"worker {W} resuming at null {start_i} [{time.time()-t0:.0f}s]", flush=True)
    ss = np.random.SeedSequence(MASTER_SEED)
    seeds = [int(s.generate_state(1)[0]) for s in ss.spawn(N_NULL)]
    for i in range(start_i, HI):
        ti = time.time()
        p, q = src_all.copy(), dst_all.copy()
        gs = np.random.SeedSequence(seeds[i]).spawn(len(groups))
        for gidx, gss in zip(groups, gs):
            s = int(gss.generate_state(1)[0])
            p2, q2 = _c_rewire(src_all[gidx], dst_all[gidx], n_nodes, SWAPS * len(gidx), s)
            p[gidx], q[gidx] = p2, q2
        A = sp.csr_matrix((np.ones(len(p), dtype=np.int64), (p, q)), shape=(n_nodes, n_nodes))
        A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros()
        c = fast_census.census(A)
        done_counts.append([c[k] for k in CL])
        del A, p, q; gc.collect()
        if (i + 1) % 10 == 0 or i == N_NULL - 1:
            json.dump({"params": [N_NULL, SWAPS, MASTER_SEED, W], "n_done": i + 1, "counts": done_counts},
                      open(CKPT, "w"))
        print(f"w{W} null {i+1}/{HI} [{time.time()-ti:.0f}s cum {time.time()-t0:.0f}s]", flush=True)
    json.dump({"worker": W, "lo": LO, "hi": HI, "counts": done_counts, "elapsed_s": time.time() - t0},
              open(os.path.join(OUTA, f"n3_part_w{W}.json"), "w"))
    print(f"WORKER {W} DONE [{time.time()-t0:.0f}s]", flush=True)
    return
    counts = np.array(done_counts, dtype=np.float64)
    obs = json.load(open(os.path.join(OUTA, "stage_a_analysis.json")))["observed"]
    mean, sd = counts.mean(0), counts.std(0, ddof=1)
    ob = np.array([obs[k] for k in CL], dtype=np.float64)
    z = np.where(sd > 0, (ob - mean) / sd, np.sign(ob - mean) * 1e6)
    emp = (np.abs(counts - mean) >= np.abs(ob - mean)).sum(0) + 1
    emp = emp / (len(counts) + 1)
    # BH q across 16 classes within the N3 family
    order = np.argsort(emp); q = np.empty(16)
    prev = 1.0
    for rank, j in enumerate(order[::-1]):
        val = min(prev, emp[j] * 16 / (16 - rank))
        q[j] = val; prev = val
    res = {"family": "N3 compartment-preserving (endpoint primary neuropil, per-side)", "tier": 1,
           "n_null": N_NULL, "swaps_per_edge": SWAPS, "master_seed": MASTER_SEED,
           "engine": "dp_rewire_c (C, same acceptance semantics as dp_rewire_fast; tests/test_dp_rewire_c.py + cross-check PASS)",
           "singleton_edges_fixed": n_single, "n_groups": len(groups),
           "classes": CL, "observed": ob.tolist(), "null_mean": mean.tolist(), "null_sd": sd.tolist(),
           "z": z.tolist(), "emp_p": emp.tolist(), "bh_q": q.tolist(),
           "per_class": {CL[j]: {"observed": float(ob[j]), "null_mean": float(mean[j]), "null_sd": float(sd[j]),
                                  "z": float(z[j]), "emp_p": float(emp[j]), "bh_q": float(q[j])} for j in range(16)},
           "elapsed_s": time.time() - t0}
    json.dump(res, open(os.path.join(OUTA, "n3_results.json"), "w"), indent=1)
    print(f"DONE [{time.time()-t0:.0f}s]", flush=True)

if __name__ == "__main__":
    main()
