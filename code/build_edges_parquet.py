"""Rebuild results/stage_a/edges_ge5.parquet from proofread_connections_783.feather.
numpy lexsort aggregation (fixed memory; dict and polars-streaming both OOM on 2GB box)."""
import os
import numpy as np
import pyarrow.ipc as ipc
import polars as pl

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "proofread_connections_783.feather")
OUT = os.path.join(os.path.dirname(__file__), "..", "results", "stage_a")

pres, posts, syns = [], [], []
reader = ipc.open_file(RAW)
n_rows = 0
for b in range(reader.num_record_batches):
    batch = reader.get_batch(b)
    pres.append(batch.column("pre_pt_root_id").to_numpy(zero_copy_only=False))
    posts.append(batch.column("post_pt_root_id").to_numpy(zero_copy_only=False))
    syns.append(batch.column("syn_count").to_numpy(zero_copy_only=False))
pre = np.concatenate(pres); post = np.concatenate(posts); syn = np.concatenate(syns)
del pres, posts, syns
n_rows = len(pre)
print(f"{n_rows:,} rows loaded", flush=True)

order = np.lexsort((post, pre))
pre, post, syn = pre[order], post[order], syn[order]
del order
change = np.empty(len(pre), dtype=bool)
change[0] = True
change[1:] = (pre[1:] != pre[:-1]) | (post[1:] != post[:-1])
starts = np.flatnonzero(change)
del change
totals = np.add.reduceat(syn, starts)
del syn
kp = totals >= 5
edges = pl.DataFrame({"pre_pt_root_id": pre[starts][kp], "post_pt_root_id": post[starts][kp], "syn_count": totals[kp]})
os.makedirs(OUT, exist_ok=True)
edges.write_parquet(os.path.join(OUT, "edges_ge5.parquet"))
print(f"edges_ge5.parquet: {edges.height:,} edges from {n_rows:,} rows / {len(starts):,} pairs", flush=True)
