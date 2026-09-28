"""Stage A final inference: z-scores (F1), empirical two-sided p (+1 correction),
BH FDR (A4), per null family (N1=ER, N2=DP). Input: results/stage_a/stage_a_results.json.
Output: results/stage_a/stage_a_analysis.json. Deterministic, no RNG."""
import json, sys
sys.path.insert(0, 'code')
import numpy as np
from stage_a import motif_zscores, bh_fdr

d = json.load(open('results/stage_a/stage_a_results.json'))
obs = d['observed']; names = list(obs.keys())
out = {'observed': obs, 'reciprocity': d['reciprocity'], 'modularity': d['modularity'],
       'n_communities': d['n_communities'], 'families': {}}
for fam in ['null_er', 'null_dp']:
    nulls = d[fam]
    z, mu, sd = motif_zscores(obs, nulls)
    M = np.array([[c[k] for k in names] for c in nulls], float)
    o = np.array([obs[k] for k in names], float)
    muv = M.mean(0)
    p = ((np.abs(M - muv) >= np.abs(o - muv)).sum(0) + 1) / (len(nulls) + 1)
    q = bh_fdr(p)
    out['families'][fam] = {
        'n_null': len(nulls),
        'per_class': {k: {'obs': obs[k], 'null_mu': mu[k], 'null_sd': sd[k],
                          'z': z[k], 'emp_p': float(p[i]), 'bh_q': float(q[i])}
                      for i, k in enumerate(names)},
        'note': ('empirical p at resolution floor 1/(n+1) for all classes with |z| large; '
                 'z for classes where null_sd floors at 1e-9 (ER 210/300, null counts ~0) '
                 'is a formula artifact - interpret via emp_p and counts instead.')}
json.dump(out, open('results/stage_a/stage_a_analysis.json', 'w'), indent=1)
print('wrote results/stage_a/stage_a_analysis.json')
sig_dp = [(k, v['z']) for k, v in out['families']['null_dp']['per_class'].items()]
print('DP z summary (enriched + / depleted -):')
for k, z in sorted(sig_dp, key=lambda t: -t[1]):
    print(f'  {k:5} z={z:+9.1f}')
