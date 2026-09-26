"""Seeded null-graph generators (AMENDMENT-3). Pure numpy; fully reproducible.

Null definitions unchanged from PREREGISTRATION section 3:
  N1 (DP): degree-preserving rewire of the observed graph, 10 successful
           endpoint swaps per edge, result stays simple and loopless.
           Implementation: batched swaps. Membership is checked against the
           pre-batch edge set (base minus removed plus added, tracked as
           sorted delta arrays), so a candidate colliding with an edge removed
           later in the same batch is conservatively rejected; accepted
           candidates are pairwise distinct within the batch and each edge
           index is swapped at most once per batch.
  N2 (ER): directed G(n, m), loops disallowed, exact edge count.
"""
import numpy as np


def er_null_np(n, m, seed):
    rng = np.random.default_rng(seed)
    total = n * (n - 1)
    assert m <= total
    keys = rng.choice(total, size=m, replace=False)
    pre = keys // (n - 1)
    post = keys % (n - 1)
    post = post.copy()
    post[post >= pre] += 1
    return pre.astype(np.int64), post.astype(np.int64)


def _in_sorted(k, arr):
    if len(arr) == 0:
        return np.zeros(len(k), dtype=bool)
    idx = np.searchsorted(arr, k)
    idx = np.minimum(idx, len(arr) - 1)
    return arr[idx] == k


def dp_rewire_np(pre, post, n_nodes, n_swaps, seed, batch=400_000, rebuild_at=200_000):
    rng = np.random.default_rng(seed)
    pre = pre.astype(np.int64).copy(); post = post.astype(np.int64).copy()
    E = len(pre)
    base = np.sort(pre * n_nodes + post)
    removed = np.empty(0, dtype=np.int64); added = np.empty(0, dtype=np.int64)
    accepted = 0
    while accepted < n_swaps:
        want = n_swaps - accepted
        b = min(batch, max(2 * want, 4096))
        i = rng.integers(0, E, b); j = rng.integers(0, E, b)
        kp = i != j
        i, j = i[kp], j[kp]
        a, c = pre[i], pre[j]
        d, bb = post[j], post[i]
        n1 = a * n_nodes + d
        n2 = c * n_nodes + bb
        valid = (a != d) & (c != bb) & (n1 != n2)
        for k in (n1, n2):
            present = (_in_sorted(k, base) & ~_in_sorted(k, removed)) | _in_sorted(k, added)
            valid &= ~present
        idx_i, idx_j = i[valid], j[valid]
        k1, k2 = n1[valid], n2[valid]
        flat = np.concatenate([k1, k2])
        _, fi = np.unique(flat, return_index=True)
        solo = np.zeros(len(flat), dtype=bool); solo[fi] = True
        pair_ok = solo[:len(k1)] & solo[len(k1):]
        idx_i, idx_j = idx_i[pair_ok], idx_j[pair_ok]
        both = np.concatenate([idx_i, idx_j])
        _, fi2 = np.unique(both, return_index=True)
        seen = np.zeros(len(both), dtype=bool); seen[fi2] = True
        ui = seen[:len(idx_i)] & seen[len(idx_i):]
        idx_i, idx_j = idx_i[ui], idx_j[ui]
        take = min(len(idx_i), want)
        idx_i, idx_j = idx_i[:take], idx_j[:take]
        old = np.concatenate([pre[idx_i] * n_nodes + post[idx_i],
                              pre[idx_j] * n_nodes + post[idx_j]])
        new = np.concatenate([pre[idx_i] * n_nodes + post[idx_j],
                              pre[idx_j] * n_nodes + post[idx_i]])
        removed = np.sort(np.concatenate([removed, old]))
        added = np.sort(np.concatenate([added, new]))
        post[idx_i], post[idx_j] = post[idx_j].copy(), post[idx_i].copy()
        accepted += take
        if len(removed) >= rebuild_at:
            keep = ~_in_sorted(base, removed)
            base = np.sort(np.concatenate([base[keep], added]))
            removed = np.empty(0, dtype=np.int64); added = np.empty(0, dtype=np.int64)
    return pre, post
