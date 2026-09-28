"""Independent audit of run_stage_b.assignment_polars (locked rule B1): pure-numpy
streaming running-argmax over ipc batches, graph-node filtered. ~200MB memory.
Writes results/stage_b/assignment_audit.json."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import polars as pl
from pyarrow import ipc
from run_stage_b import assignment_polars

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUTA = os.path.join(os.path.dirname(__file__), "..", "results", "stage_a")
OUT = os.path.join(os.path.dirname(__file__), "..", "results", "stage_b")

t0 = time.time()
edges = pl.read_parquet(os.path.join(OUTA, "edges_ge5.parquet"))
nodes = np.unique(pl.concat([edges["pre_pt_root_id"], edges["post_pt_root_id"]]).unique().to_numpy())
print(f"graph nodes {len(nodes):,}", flush=True)

# alphabetical interning up front: tie-break must match the documented rule
# (neuropil name ascending); first-seen order would diverge on full ties.
_names = set()
for _p in ("per_neuron_neuropil_count_pre_783.feather", "per_neuron_neuropil_count_post_783.feather"):
    _r = ipc.open_file(os.path.join(RAW, _p))
    for _bi in range(_r.num_record_batches):
        _names.update(_r.get_batch(_bi).column("neuropil").to_pylist())
neu_codes = {n: i for i, n in enumerate(sorted(_names))}
def intern(arr):
    return np.array([neu_codes[s] for s in arr], dtype=np.int32)

# pre table (small) -> dict (root_idx, neu_code) -> count_pre
r = ipc.open_file(os.path.join(RAW, "per_neuron_neuropil_count_pre_783.feather"))
pre_d = {}
for bi in range(r.num_record_batches):
    b = r.get_batch(bi)
    root = b.column("pre_pt_root_id").to_numpy(); neu = b.column("neuropil").to_pylist()
    cnt = b.column("count").to_numpy()
    m = np.isin(root, nodes)
    ri = np.searchsorted(nodes, root[m])
    nc = intern([neu[i] for i in np.flatnonzero(m)])
    for a, bb, c in zip(ri, nc, cnt[m]):
        pre_d[(int(a), int(bb))] = pre_d.get((int(a), int(bb)), 0) + int(c)
print(f"pre pairs {len(pre_d):,} [{time.time()-t0:.0f}s]", flush=True)

post_pairs = set()
best_total = np.full(len(nodes), -1, dtype=np.int64)
best_pre = np.full(len(nodes), -1, dtype=np.int64)
best_neu = np.full(len(nodes), -1, dtype=np.int32)

r = ipc.open_file(os.path.join(RAW, "per_neuron_neuropil_count_post_783.feather"))
for bi in range(r.num_record_batches):
    b = r.get_batch(bi)
    root = b.column("post_pt_root_id").to_numpy(); neu = b.column("neuropil").to_pylist()
    cnt = b.column("count").to_numpy()
    m = np.isin(root, nodes)
    if not m.any():
        continue
    ri = np.searchsorted(nodes, root[m])
    nc = intern([neu[i] for i in np.flatnonzero(m)])
    for a, bb in zip(ri, nc):
        post_pairs.add((int(a), int(bb)))
    cp = np.array([pre_d.get((int(a), int(bb)), 0) for a, bb in zip(ri, nc)], dtype=np.int64)
    tot = cp + cnt[m]
    order = np.lexsort((nc, -cp, -tot, ri))
    ri, nc, cp, tot = ri[order], nc[order], cp[order], tot[order]
    first = np.flatnonzero(np.r_[True, ri[1:] != ri[:-1]])
    cr, cn, cc, ct = ri[first], nc[first], cp[first], tot[first]
    upd = (ct > best_total[cr]) | ((ct == best_total[cr]) & (cc > best_pre[cr])) | \
          ((ct == best_total[cr]) & (cc == best_pre[cr]) & (cn < best_neu[cr]))
    best_total[cr[upd]] = ct[upd]; best_pre[cr[upd]] = cc[upd]; best_neu[cr[upd]] = cn[upd]
    if bi % 100 == 0:
        print(f"batch {bi} [{time.time()-t0:.0f}s]", flush=True)

# pre-only (root,neuropil) pairs: candidates with total = count_pre, post = 0
n_preonly = 0
for (a, bb), c in pre_d.items():
    if (a, bb) not in post_pairs:
        n_preonly += 1
        if (c > best_total[a] or (c == best_total[a] and c > best_pre[a]) or
                (c == best_total[a] and c == best_pre[a] and bb < best_neu[a])):
            best_total[a] = c; best_pre[a] = c; best_neu[a] = bb
print(f"pre-only candidates {n_preonly:,}", flush=True)

code_to_neu = {v: k for k, v in neu_codes.items()}
have = best_total >= 0
st = {int(nodes[i]): (code_to_neu[int(best_neu[i])], int(best_total[i])) for i in np.flatnonzero(have)}
print(f"streaming roots {len(st):,} [{time.time()-t0:.0f}s]", flush=True)

a_pl = assignment_polars(os.path.join(RAW, "per_neuron_neuropil_count_pre_783.feather"),
                         os.path.join(RAW, "per_neuron_neuropil_count_post_783.feather"),
                         keep_roots=nodes)
n_neu = n_cnt = 0
bad_roots = []
for row in a_pl.itertuples(index=False):
    rid = int(row.root_id)
    if rid not in st:
        n_neu += 1; continue
    sneu, stot = st[rid]
    if sneu != row.primary_neuropil: n_neu += 1
    if stot != int(row.primary_count): n_cnt += 1; bad_roots.append((rid, sneu, stot, row.primary_neuropil, int(row.primary_count)))
print('count-mismatch examples (root, audit_neu, audit_total, polars_neu, polars_total):')
for b in bad_roots[:10]: print(' ', b)
json.dump([list(map(str,b)) for b in bad_roots[:50]], open('/tmp/count_mismatch_roots.json','w'))
verdict = "PASS" if n_neu == 0 and n_cnt == 0 and len(st) == len(a_pl) else "FAIL"
print(f"roots compared {len(a_pl):,} (streaming {len(st):,}); neuropil mismatches {n_neu}; count mismatches {n_cnt}; AUDIT {verdict}")
os.makedirs(OUT, exist_ok=True)
json.dump({"check": "assignment_polars vs independent numpy streaming running-argmax, full tables, graph-node filtered",
           "roots_compared": len(a_pl), "roots_streaming": len(st),
           "neuropil_mismatches": n_neu, "count_mismatches": n_cnt, "verdict": verdict,
           "date": "2026-09-29"},
          open(os.path.join(OUT, "assignment_audit.json"), "w"), indent=1)
