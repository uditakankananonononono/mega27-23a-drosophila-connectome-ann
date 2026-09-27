"""Stage A runner v4b: backward DP worker (max-capacity directive 2026-09-27).
Computes DP nulls 99..0 descending into a SEPARATE checkpoint file; merged into
the primary stage_a_results.json externally. Same master seed, same seed_list,
same nulls.py/fast_census.py functions => results must be bit-identical to the
primary's forward computation; merge step asserts equality on any overlap.
Never touches the primary checkpoint."""
import json, os, sys, time
import numpy as np
import polars as pl
import scipy.sparse as sp
sys.path.insert(0, os.path.dirname(__file__))
import fast_census, nulls

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "stage_a")
N_NULL = 100
MASTER_SEED = 23
CKPT = os.path.join(OUT, "stage_a_results_b.json")

def save(res):
    tmp = CKPT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(res, f)
    os.replace(tmp, CKPT)

def csr_from_arrays(pre, post, n):
    A = sp.csr_matrix((np.ones(len(pre), dtype=np.int64), (pre, post)), shape=(n, n))
    A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros()
    return A

def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    import hashlib, scipy, subprocess
    prov = dict(git=subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True,cwd=os.path.dirname(__file__)).stdout.strip(),
                numpy=np.__version__, scipy=scipy.__version__,
                edges_sha256=hashlib.sha256(open(os.path.join(OUT,"edges_ge5.parquet"),"rb").read()).hexdigest())
    edges = pl.read_parquet(os.path.join(OUT, "edges_ge5.parquet"))
    nodes = pl.concat([edges["pre_pt_root_id"], edges["post_pt_root_id"]]).unique().to_numpy()
    index = {r: i for i, r in enumerate(nodes)}
    src = np.fromiter((index[r] for r in edges["pre_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    dst = np.fromiter((index[r] for r in edges["post_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    n = len(nodes)
    key = src * n + dst
    _, ui = np.unique(key, return_index=True)
    src, dst = src[ui], dst[ui]
    kp = src != dst
    src, dst = src[kp], dst[kp]
    A = csr_from_arrays(src, dst, n)
    E = A.nnz
    del A
    print(f"B graph: {n:,} nodes, {E:,} edges [{time.time()-t0:.0f}s]", flush=True)

    prev = {}
    if os.path.exists(CKPT):
        try:
            prev = json.load(open(CKPT))
        except Exception:
            prev = {}
    resume_ok = prev.get("params", {}).get("runner") == "v4b-backward"
    done = dict(prev.get("null_dp_b", {})) if resume_ok else {}
    res = dict(provenance=prov,
               params=dict(runner="v4b-backward", threshold=5, n_null=N_NULL, master_seed=MASTER_SEED,
                           nulls_impl="code/nulls.py seeded numpy (AMENDMENT-3)",
                           note="backward DP worker; merge into primary externally"))

    ss = np.random.SeedSequence(MASTER_SEED)
    seeds = [int(s.generate_state(1)[0]) for s in ss.spawn(2 * N_NULL)]
    res["params"]["seed_list"] = seeds
    if done:
        print(f"B resuming: {len(done)} DP nulls done", flush=True)
    for i in range(N_NULL - 1, -1, -1):
        if str(i) in done:
            continue
        p1, q1 = nulls.dp_rewire_np(src, dst, n, 10 * E, seed=seeds[i])
        done[str(i)] = fast_census.census(csr_from_arrays(p1, q1, n))
        res["null_dp_b"] = done
        save(res)
        print(f"B DP null idx {i} done ({len(done)}/{N_NULL}) [{time.time()-t0:.0f}s]", flush=True)
    print("B DONE", flush=True)

if __name__ == "__main__":
    main()
