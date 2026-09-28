"""Stage B stratified summary: per-class enriched/depleted neuropil counts (|z|>3),
median/min/max z vs each null family. Deterministic. Writes results/stage_b/stage_b_summary.json."""
import json, sys
import numpy as np

d = json.load(open('results/stage_b/stage_b_results.json'))
n = d['neuropils']; names = sorted(n.keys())
classes = ['003','012','102','021D','021U','021C','111D','111U','030T','030C','201','120D','120U','120C','210','300']
out = {'n_neuropils': len(names), 'families': {}}
for fam in ('z_dp', 'z_er'):
    per = {}
    for c in classes:
        zs = np.nan_to_num(np.array([n[k][fam][c] for k in names], dtype=float), nan=0.0)
        per[c] = {'enriched_gt3': int((zs > 3).sum()), 'depleted_lt-3': int((zs < -3).sum()),
                  'median_z': float(np.median(zs)), 'min_z': float(zs.min()), 'max_z': float(zs.max())}
    out['families'][fam] = per
out['ffl_030T_by_neuropil'] = sorted(
    ({'neuropil': k, 'z_dp': n[k]['z_dp']['030T'], 'n': n[k]['n']} for k in names),
    key=lambda r: -r['z_dp'])
out['note'] = ('z uses sd floored at 1e-9 (F1); classes with near-zero null counts produce '
               'astronomical z (see max_z) - interpret via enriched/depleted counts and medians. '
               'Permutation test (stage_b.permutation_test_class_difference) not yet run - tracked gap.')
json.dump(out, open('results/stage_b/stage_b_summary.json', 'w'), indent=1)
print('wrote results/stage_b/stage_b_summary.json')
