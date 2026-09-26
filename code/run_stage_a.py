"""Stage A runner (locked spec, PREREGISTRATION.md sections 2-3).
Streaming aggregation (polars) -> igraph -> observed stats + 2x100 null censuses.
Writes results/stage_a/stage_a_results.json + edges parquet for reuse."""
import json, os, sys, time
import numpy as np
import polars as pl
sys.path.insert(0, os.path.dirname(__file__))
import stage_a

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUT = os.path.join(os.path.dirname(__file__), "..", "results", "stage_a")
N_NULL = 100
MASTER_SEED = 23
NT_COLS = ["gaba_avg", "ach_avg", "glut_avg", "oct_avg", "ser_avg", "da_avg"]

def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    import duckdb, pyarrow as pa, pyarrow.ipc as ipc, pyarrow.parquet as pq
    pq_path = os.path.join(OUT, "connections_783_stream.parquet")
    if not os.path.exists(pq_path):
        _f = ipc.open_file(os.path.join(RAW, "proofread_connections_783.feather"))
        wtr = None
        for i in range(_f.num_record_batches):
            b = _f.get_batch(i)
            if wtr is None:
                wtr = pq.ParquetWriter(pq_path, b.schema, compression="zstd")
            wtr.write_batch(b)
        wtr.close()
        print(f"parquet staged [{time.time()-t0:.0f}s]", flush=True)
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='1200MB'")
    con.execute(f"PRAGMA temp_directory='{OUT}'")
    nt_expr = ", ".join(f"SUM({c} * syn_count) AS {c}_w" for c in NT_COLS)
    q = f"""SELECT pre_pt_root_id, post_pt_root_id, SUM(syn_count) AS syn_sum, {nt_expr}
            FROM '{pq_path}' GROUP BY 1, 2 HAVING SUM(syn_count) >= 5"""
    edges = con.execute(q).pl()
    print(f"edges at >=5: {edges.height:,} [{time.time()-t0:.0f}s]", flush=True)
    edges.write_parquet(os.path.join(OUT, "edges_ge5.parquet"))

    import igraph as ig
    nodes = pl.concat([edges["pre_pt_root_id"], edges["post_pt_root_id"]]).unique().to_numpy()
    index = {r: i for i, r in enumerate(nodes)}
    src = np.fromiter((index[r] for r in edges["pre_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    dst = np.fromiter((index[r] for r in edges["post_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    g = ig.Graph(n=len(nodes), edges=list(zip(src.tolist(), dst.tolist())), directed=True)
    g.vs["root_id"] = nodes.tolist()
    print(f"graph: {g.vcount():,} nodes, {g.ecount():,} edges [{time.time()-t0:.0f}s]", flush=True)

    obs = stage_a.triad_census(g)
    t_census = time.time() - t0
    rec = stage_a.reciprocity_binary(g)
    deg = g.degree(mode="all")
    ks = sorted(set(int(x) for x in np.percentile(deg, [50, 75, 90, 95, 99])))
    rc = stage_a.rich_club_coefficient(g, ks)
    comm = g.community_multilevel(weights=None, return_levels=False)
    modularity = comm.modularity
    n_comms = len(set(comm.membership))
    print(f"observed stats done (census {t_census:.0f}s) [{time.time()-t0:.0f}s]", flush=True)

    null1, null2 = [], []
    ss = np.random.SeedSequence(MASTER_SEED)
    seeds = [int(s.generate_state(1)[0]) for s in ss.spawn(2 * N_NULL)]
    for i in range(N_NULL):
        h1 = stage_a.degree_preserving_null(g, n_swaps_per_edge=10, seed=seeds[i])
        null1.append(stage_a.triad_census(h1)); del h1
        h2 = stage_a.er_null(g.vcount(), g.ecount(), seed=seeds[N_NULL + i])
        null2.append(stage_a.triad_census(h2)); del h2
        print(f"nulls {i+1}/{N_NULL} [{time.time()-t0:.0f}s]", flush=True)

    z1, mu1, sd1 = stage_a.motif_zscores(obs, null1)
    z2, mu2, sd2 = stage_a.motif_zscores(obs, null2)
    res = dict(
        params=dict(threshold=5, n_null=N_NULL, master_seed=MASTER_SEED,
                    n_nodes=g.vcount(), n_edges=g.ecount(), census_seconds=t_census),
        observed=obs, reciprocity=rec, rich_club={str(k): v for k, v in rc.items()},
        degree_percentile_ks=ks, modularity=modularity, n_communities=n_comms,
        z_vs_degree_preserving=z1, z_vs_er=z2,
        null1_mean=mu1, null1_sd=sd1, null2_mean=mu2, null2_sd=sd2,
        elapsed_s=time.time() - t0)
    with open(os.path.join(OUT, "stage_a_results.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(f"DONE [{time.time()-t0:.0f}s]", flush=True)

if __name__ == "__main__":
    main()
