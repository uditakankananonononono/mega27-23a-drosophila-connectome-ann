"""N3 compartment-preserving null (AMENDMENT-2 A1, renamed AMENDMENT-4 A14).
Preserves per-neuron in/out degree AND each endpoint's primary neuropil:
edges are grouped by (pre neuron's primary pre-side neuropil, post neuron's
primary post-side neuropil) and each group is rewired independently with the
seeded batched swapper (code/nulls.dp_rewire_np). Per-group degree
preservation implies global degree preservation. Singleton groups are left
fixed (honest limitation: their edges are unrewirable under N3).
"""
import numpy as np
import nulls

def primary_neuropil(table_root, table_neuropil, table_count):
    """Arrays (root_id, neuropil, count) -> dict root_id -> primary neuropil (argmax count)."""
    best = {}
    for r, npil, c in zip(table_root, table_neuropil, table_count):
        r = int(r)
        cur = best.get(r)
        if cur is None or c > cur[1]:
            best[r] = (npil, int(c))
    return {r: v[0] for r, v in best.items()}

def edge_compartments(pre_ids, post_ids, pre_prim, post_prim, default="NONE"):
    """Return arrays of compartment labels for each edge."""
    a = np.array([pre_prim.get(int(r), default) for r in pre_ids])
    b = np.array([post_prim.get(int(r), default) for r in post_ids])
    return a, b

def n3_rewire(pre, post, comp_pre, comp_post, n_nodes, swaps_per_edge, seed):
    """Group edges by (comp_pre, comp_post); rewire each group independently."""
    rng_ss = np.random.SeedSequence(seed)
    groups = {}
    for i in range(len(pre)):
        groups.setdefault((comp_pre[i], comp_post[i]), []).append(i)
    keys = sorted(groups.keys())
    seeds = [int(s.generate_state(1)[0]) for s in rng_ss.spawn(len(keys))]
    out_pre, out_post = pre.copy(), post.copy()
    stats = dict(n_groups=len(keys), n_singleton=0, n_rewired_groups=0)
    for k, s in zip(keys, seeds):
        idx = np.array(groups[k], dtype=np.int64)
        if len(idx) < 2:
            stats["n_singleton"] += 1
            continue
        p2, q2 = nulls.dp_rewire_np(pre[idx], post[idx], n_nodes,
                                    swaps_per_edge * len(idx), seed=s)
        out_pre[idx], out_post[idx] = p2, q2
        stats["n_rewired_groups"] += 1
    return out_pre, out_post, stats
