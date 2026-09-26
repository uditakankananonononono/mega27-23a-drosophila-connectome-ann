"""Graph construction from FlyWire v783 release files (locked spec: PREREGISTRATION.md section 2)."""
import numpy as np
import pandas as pd
import pyarrow.feather as pf

EDGE_THRESHOLD = 5  # >=5 synapses, Dorkenwald et al. 2024 standard; locked pre-analysis


def load_connections(path, columns=None):
    """Memory-mapped column read of the proofread connections table."""
    return pf.read_table(path, columns=columns, memory_map=True).to_pandas()


def aggregate_edges(df, pre_col="pre_pt_root_id", post_col="post_pt_root_id", count_col="syn_count"):
    """Sum synapse counts over neuropils per (pre, post) pair."""
    agg = df.groupby([pre_col, post_col], sort=False)[count_col].sum().reset_index()
    return agg


def threshold_edges(agg, threshold=EDGE_THRESHOLD):
    return agg[agg[count_col_name(agg)] >= threshold].reset_index(drop=True)


def count_col_name(agg):
    return [c for c in agg.columns if c not in ("pre_pt_root_id", "post_pt_root_id")][0]


def build_arrays(agg, pre_col="pre_pt_root_id", post_col="post_pt_root_id"):
    """Return (node_ids, src_idx, dst_idx, weights) with contiguous integer node indexing."""
    nodes = pd.unique(pd.concat([agg[pre_col], agg[post_col]]))
    index = pd.Series(np.arange(len(nodes)), index=nodes)
    src = index[agg[pre_col].to_numpy()].to_numpy()
    dst = index[agg[post_col].to_numpy()].to_numpy()
    w = agg[count_col_name(agg)].to_numpy()
    return nodes, src, dst, w


def to_igraph(nodes, src, dst, w=None):
    import igraph as ig
    g = ig.Graph(n=len(nodes), edges=list(zip(src, dst)), directed=True)
    g.vs["root_id"] = nodes.tolist() if hasattr(nodes, "tolist") else list(nodes)
    if w is not None:
        g.es["weight"] = np.asarray(w, dtype=float).tolist()
    return g
