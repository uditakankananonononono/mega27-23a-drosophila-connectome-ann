"""Stage C graph exports (deterministic, pre-training): whole-brain, degree-preserving
shuffled (C engine, fixed seed), and neuropil-block modular export. npz, gitignored."""
import ctypes, os, sys
import numpy as np
import polars as pl
import pandas as pd

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..", "..")
LIB = ctypes.CDLL(os.path.join(ROOT, "code", "dp_rewire_c.so"))
LIB.dp_rewire_c.restype = ctypes.c_longlong
LIB.dp_rewire_c.argtypes = [ctypes.c_void_p]*3 + [ctypes.c_longlong]*2 + [ctypes.c_uint64]

edges = pl.read_parquet(os.path.join(ROOT, "results", "stage_a", "edges_ge5.parquet"))
nodes = np.unique(pl.concat([edges["pre_pt_root_id"], edges["post_pt_root_id"]]).unique().to_numpy())
idx = {r: i for i, r in enumerate(nodes)}
src = np.fromiter((idx[r] for r in edges["pre_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
dst = np.fromiter((idx[r] for r in edges["post_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
n = len(nodes)
np.savez_compressed(os.path.join(ROOT, "exports", "fly_graph_whole.npz"),
                    src=src.astype(np.int32), dst=dst.astype(np.int32), n_nodes=n)
p, q = src.astype(np.int64).copy(), dst.astype(np.int64).copy()
acc = LIB.dp_rewire_c(p.ctypes.data, q.ctypes.data, len(p), n, 10 * len(p), 260000)
assert acc == 10 * len(p)
np.savez_compressed(os.path.join(ROOT, "exports", "fly_graph_dp_shuffled.npz"),
                    src=p.astype(np.int32), dst=q.astype(np.int32), n_nodes=n)
# modular: blocks from primary neuropil assignment
OPTIC = ("ME_", "LA_", "LO_", "LOP_", "AME_", "OC_")
CENTRAL = ("EB", "PB", "FB", "NO_", "AB_")
asg = pd.read_csv(os.path.join(ROOT, "results", "stage_b", "neuropil_assignment.csv"))
npil = dict(zip(asg.root_id, asg.primary_neuropil))
block = np.zeros(n, dtype=np.int8) + 2
for i, r in enumerate(nodes):
    nm = npil.get(int(r), "")
    if nm.startswith(OPTIC): block[i] = 0
    elif nm.startswith(CENTRAL): block[i] = 1
np.savez_compressed(os.path.join(ROOT, "exports", "fly_graph_modular.npz"),
                    src=src.astype(np.int32), dst=dst.astype(np.int32), n_nodes=n, block=block)
print("exports:", {f: os.path.getsize(os.path.join(ROOT, "exports", f)) for f in os.listdir(os.path.join(ROOT, "exports"))})
print("block counts:", np.bincount(block).tolist())
