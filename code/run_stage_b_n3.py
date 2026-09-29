"""Stage B N3 arm (Tier 2, A1 'within Stage B'): per-neuropil compartment-preserving
nulls, 25 replicates each, master_seed 27. Compartments = (pre-side primary, post-side
primary) of endpoints; within one neuropil most edges share a compartment, so the
constraint is near-degenerate there (N3 ~= N1) - reported honestly, per-spec.
z/emp_p per neuropil per class vs observed (stage_b_results.json). C engine."""
import json, os, sys, time, gc
import numpy as np
import polars as pl
import pandas as pd
from pyarrow import ipc as _ipc
import ctypes
import scipy.sparse as sp
sys.path.insert(0, os.path.dirname(__file__))
import fast_census

ROOT = os.path.join(os.path.dirname(__file__), "..")
LIB = ctypes.CDLL(os.path.join(ROOT, "code", "dp_rewire_c.so"))
LIB.dp_rewire_c.restype = ctypes.c_longlong
LIB.dp_rewire_c.argtypes = [ctypes.c_void_p]*3 + [ctypes.c_longlong]*2 + [ctypes.c_uint64]
CL = ['003','012','102','021D','021U','021C','111D','111U','030T','030C','201','120D','120U','120C','210','300']
N_NULL, SWAPS, MASTER = 25, 10, 27

def side_primary(path, idcol, keep):
    keep = set(int(r) for r in keep); best = {}
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
    edges = pl.read_parquet(os.path.join(ROOT, "results", "stage_a", "edges_ge5.parquet"))
    nodes = np.unique(pl.concat([edges["pre_pt_root_id"], edges["post_pt_root_id"]]).unique().to_numpy())
    pre_prim = side_primary(os.path.join(ROOT, "data", "raw", "per_neuron_neuropil_count_pre_783.feather"), "pre_pt_root_id", nodes)
    post_prim = side_primary(os.path.join(ROOT, "data", "raw", "per_neuron_neuropil_count_post_783.feather"), "post_pt_root_id", nodes)
    asg = pd.read_csv(os.path.join(ROOT, "results", "stage_b", "neuropil_assignment.csv"))
    npil = dict(zip(asg.root_id, asg.primary_neuropil))
    obs_b = json.load(open(os.path.join(ROOT, "results", "stage_b", "stage_b_results.json")))["neuropils"]
    pre_r = edges["pre_pt_root_id"].to_numpy(); post_r = edges["post_pt_root_id"].to_numpy()
    del edges; gc.collect()
    out = {"n_null": N_NULL, "swaps_per_edge": SWAPS, "master_seed": MASTER,
           "engine": "dp_rewire_c", "note": "Tier 2; near-degenerate where endpoints share compartments",
           "neuropils": {}}
    names = sorted(obs_b.keys())
    for ni, name in enumerate(names):
        ts = time.time()
        members = set(r for r, v in npil.items() if v == name)
        emask = np.array([(int(a) in members) and (int(b) in members) for a, b in zip(pre_r, post_r)])
        sub_nodes = np.unique(np.concatenate([pre_r[emask], post_r[emask]]))
        nn = len(sub_nodes)
        idx = {r: i for i, r in enumerate(sub_nodes)}
        s = np.fromiter((idx[int(r)] for r in pre_r[emask]), dtype=np.int64, count=int(emask.sum()))
        d = np.fromiter((idx[int(r)] for r in post_r[emask]), dtype=np.int64, count=int(emask.sum()))
        comps = {}
        cp = [pre_prim.get(int(r), "NONE") for r in pre_r[emask]]
        cq = [post_prim.get(int(r), "NONE") for r in post_r[emask]]
        for i in range(len(s)):
            comps.setdefault((cp[i], cq[i]), []).append(i)
        groups = [np.array(v, dtype=np.int64) for v in comps.values() if len(v) >= 2]
        counts = []
        ss = np.random.SeedSequence(MASTER + ni)
        seeds = [int(x.generate_state(1)[0]) for x in ss.spawn(N_NULL)]
        for k in range(N_NULL):
            p, q = s.copy(), d.copy()
            gs = np.random.SeedSequence(seeds[k]).spawn(len(groups))
            for gidx, gss in zip(groups, gs):
                gseed = int(gss.generate_state(1)[0])
                p2 = s[gidx].astype(np.int64).copy(); q2 = d[gidx].astype(np.int64).copy()
                acc = LIB.dp_rewire_c(p2.ctypes.data, q2.ctypes.data, len(p2), nn, SWAPS * len(gidx), gseed)
                p[gidx], q[gidx] = p2, q2
            A = sp.csr_matrix((np.ones(len(p), dtype=np.int64), (p, q)), shape=(nn, nn))
            A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros()
            c = fast_census.census(A)
            counts.append([c[kk] for kk in CL])
        counts = np.array(counts, dtype=np.float64)
        ob = np.array([obs_b[name]["observed"][kk] for kk in CL], dtype=np.float64)
        mean, sd = counts.mean(0), counts.std(0, ddof=1)
        z = np.where(sd > 0, (ob - mean) / sd, np.sign(ob - mean) * 1e6)
        emp = ((np.abs(counts - mean) >= np.abs(ob - mean)).sum(0) + 1) / (N_NULL + 1)
        out["neuropils"][name] = {"n_groups": len(groups), "n_neurons": nn,
            "per_class": {CL[j]: {"z": float(z[j]), "emp_p": float(emp[j])} for j in range(16)}}
        print(f"{ni+1}/51 {name} n={nn} groups={len(groups)} [{time.time()-ts:.0f}s cum {time.time()-t0:.0f}s]", flush=True)
        if (ni + 1) % 10 == 0:
            json.dump(out, open(os.path.join(ROOT, "results", "stage_b", "stage_b_n3.json"), "w"), indent=1)
    json.dump(out, open(os.path.join(ROOT, "results", "stage_b", "stage_b_n3.json"), "w"), indent=1)
    print(f"DONE [{time.time()-t0:.0f}s]", flush=True)

if __name__ == "__main__":
    main()
