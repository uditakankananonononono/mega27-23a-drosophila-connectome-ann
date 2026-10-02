"""Summarize results/stage_b/fournode_motifs.json by structural features of each isoclass (igraph Graph.Isoclass(4, i, directed=True))."""
import json, numpy as np, igraph as ig
d = {}
for f in ("results/stage_b/fournode_motifs.json", "results/stage_b/fournode_motifs_b.json"):
    d.update(json.load(open(f)))
Z = np.array([[np.nan if v is None else v for v in r["z"]] for r in d.values()])
feat = {}
for i in range(218):
    try: g = ig.Graph.Isoclass(4, i, directed=True)
    except Exception: continue
    E = set(g.get_edgelist()); feat[i] = (len(E), sum(1 for (a, b) in E if (b, a) in E and a < b), g.is_connected(mode="weak"))
tested = [i for i in feat if feat[i][2] and np.sum(~np.isnan(Z[:, i])) >= 0.75 * len(d)]
up = [i for i in tested if (Z[:, i] > 3).sum() >= 0.75 * len(d) and (Z[:, i] < -3).sum() == 0]
dn = [i for i in tested if (Z[:, i] < -3).sum() >= 0.75 * len(d) and (Z[:, i] > 3).sum() == 0]
res = {"neuropils": list(d), "n_connected_classes": sum(1 for f in feat.values() if f[2]), "tested_ge6": len(tested), "consistently_enriched": len(up), "consistently_depleted": len(dn),
       "enriched_edges_mutual": sorted((feat[i][0], feat[i][1]) for i in up), "depleted_edges_mutual": sorted((feat[i][0], feat[i][1]) for i in dn),
       "median_z_by_mutual_dyads": {m: float(np.nanmedian(np.nanmedian(Z[:, [i for i in tested if feat[i][1] == m]], axis=0))) for m in range(5) if any(feat[i][1] == m for i in tested)},
       "median_z_by_edges": {k: float(np.nanmedian(np.nanmedian(Z[:, [i for i in tested if feat[i][0] == k]], axis=0))) for k in range(3, 11) if any(feat[i][0] == k for i in tested)}}
json.dump(res, open("results/stage_b/fournode_summary.json", "w"), indent=1); print(json.dumps(res))
