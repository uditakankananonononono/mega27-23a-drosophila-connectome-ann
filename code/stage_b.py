"""Stage B: neuropil assignment + stratified motif analysis (PREREGISTRATION.md section 4)."""
import numpy as np
import pandas as pd
import polars as pl
import pyarrow.feather as pf

MIN_NEUROPIL_NEURONS = 200  # locked: per-neuropil subgraphs must have >=200 neurons to be testable


def assign_primary_neuropil(pre_path, post_path):
    """Neuron -> neuropil with largest pre+post synapse count (ties: pre count). Locked rule B1."""
    frames = []
    for path, idcol, cnt in ((pre_path, "pre_pt_root_id", "count"), (post_path, "post_pt_root_id", "count")):
        t = pf.read_table(path, memory_map=True).to_pandas()
        t = t.rename(columns={idcol: "root_id", "count": cnt})
        frames.append(t)
    pre, post = frames
    m = pre.merge(post, on=["root_id", "neuropil"], how="outer", suffixes=("_pre", "_post")).fillna(0)
    m["total"] = m["count_pre"] + m["count_post"]
    m = m.sort_values(["root_id", "total", "count_pre"], ascending=[True, False, False])
    top = m.drop_duplicates("root_id", keep="first")[["root_id", "neuropil", "total"]]
    return top.rename(columns={"neuropil": "primary_neuropil", "total": "primary_count"})


def neuropil_subgraph_mask(node_root_ids, assignment):
    """Return dict neuropil -> boolean mask over graph nodes (assignment may miss nodes)."""
    amap = dict(zip(assignment["root_id"], assignment["primary_neuropil"]))
    labels = np.array([amap.get(r, None) for r in node_root_ids], dtype=object)
    out = {}
    for np_name in pd.unique(labels[labels != None]):
        mask = labels == np_name
        if mask.sum() >= MIN_NEUROPIL_NEURONS:
            out[np_name] = mask
    return out


def permutation_test_class_difference(group_stats, labels, n_perm=10000, seed=23):
    """B3: do motif-enrichment profiles differ across neuropil classes?
    group_stats: dict neuropil -> statistic vector (np.array). labels: dict neuropil -> class.
    Statistic: sum of within-class pairwise Euclidean distances minus between-class (ANOVA-like)."""
    rng = np.random.default_rng(seed)
    nps = list(group_stats)
    X = np.array([group_stats[k] for k in nps])
    lab = np.array([labels[k] for k in nps])

    def stat(lab_vec):
        within, between = 0.0, 0.0
        for i in range(len(X)):
            for j in range(i + 1, len(X)):
                d = np.linalg.norm(X[i] - X[j])
                if lab_vec[i] == lab_vec[j]:
                    within += d
                else:
                    between += d
        return between - within

    obs = stat(lab)
    cnt = 0
    for _ in range(n_perm):
        if stat(rng.permutation(lab)) >= obs:
            cnt += 1
    return obs, (cnt + 1) / (n_perm + 1)
