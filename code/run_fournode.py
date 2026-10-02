"""4-node directed motif census (igraph motifs_randesu size=4, 218 classes) per neuropil induced subgraph (>=5 syn edges, primary-neuropil assignment),
vs N1 degree-preserving nulls (10 swaps/edge, 10 nulls, seeded). Exploratory, small neuropils only (census cost grows steeply with edge count). z=(obs-mu)/sd."""
import sys, json, time, numpy as np, pandas as pd, igraph as ig
sys.path.insert(0, "code"); import nulls
a = pd.read_csv("results/stage_b/neuropil_assignment.csv"); e = pd.read_parquet("results/stage_a/edges_ge5.parquet")
NN = 10; out = {}
for np_ in sys.argv[1:]:
    ids = set(a.root_id[a.primary_neuropil == np_]); s = e[e.pre_pt_root_id.isin(ids) & e.post_pt_root_id.isin(ids)]
    u, inv = np.unique(np.concatenate([s.pre_pt_root_id.values, s.post_pt_root_id.values]), return_inverse=True)
    n = len(u); p = inv[:len(s)].astype(np.int64); q = inv[len(s):].astype(np.int64)
    cen = lambda x, y: np.array(ig.Graph(n=n, edges=list(zip(x.tolist(), y.tolist())), directed=True).motifs_randesu(size=4), dtype=float)
    t0 = time.time(); obs = cen(p, q); nl = []
    for k in range(NN):
        x, y = nulls.dp_rewire_fast(p.copy(), q.copy(), n, 10 * len(p), 9000 + k); nl.append(cen(x, y))
    N = np.array(nl); mu = N.mean(0); sd = N.std(0, ddof=1)
    ok = (~np.isnan(obs)) & (sd > 0)
    z = np.where(ok, (obs - mu) / np.where(sd > 0, sd, 1), np.nan)
    out[np_] = {"n_nodes": n, "n_edges": int(len(p)), "n_null": NN, "obs": [None if np.isnan(v) else float(v) for v in obs], "mu": mu.tolist(), "sd": sd.tolist(), "z": [None if np.isnan(v) else float(v) for v in z], "secs": round(time.time() - t0)}
    json.dump(out, open("results/stage_b/fournode_motifs.json", "w"))
    print(np_, n, len(p), "classes tested", int(ok.sum()), "|z|>3:", int((np.abs(z[ok]) > 3).sum()), round(time.time() - t0), flush=True)
