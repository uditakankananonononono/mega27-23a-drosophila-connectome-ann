import json, time
import polars as pl
import igraph as ig
import numpy as np

t0=time.time()
edges = pl.read_parquet('results/stage_a/edges_ge5.parquet')
cols = edges.columns
print('cols', cols)
# build node index
src = edges[cols[0]].to_numpy(); dst = edges[cols[1]].to_numpy()
nodes = np.unique(np.concatenate([src, dst]))
idx = {r:i for i,r in enumerate(nodes)}
import pandas as pd
s = pd.Index(nodes)
ei = s.get_indexer(src); di = s.get_indexer(dst)
g = ig.Graph(n=len(nodes), edges=list(zip(ei.tolist(), di.tolist())), directed=True)
print('graph', g.vcount(), g.ecount(), 'build_s', round(time.time()-t0,1))
t1=time.time()
tc = g.triad_census()
print('census_s', round(time.time()-t1,1))
names = ['003','012','102','021D','021U','021C','111D','111U','030T','030C','201','120D','120U','120C','210','300']
ig_counts = dict(zip(names, [int(x) for x in tc]))
d = json.load(open('results/stage_a/stage_a_results.json'))
obs = d['observed']
print(f'{"class":6} {"fast_census":>18} {"igraph":>18} match')
ok=True
for k in names:
    m = obs[k]==ig_counts[k]
    ok &= m
    print(f'{k:6} {obs[k]:>18} {ig_counts[k]:>18} {m}')
print('ALL MATCH' if ok else 'MISMATCH FOUND')
