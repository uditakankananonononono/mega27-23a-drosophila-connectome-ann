import json, os, sys, numpy as np
sys.path.insert(0, 'code')
import stage_b
d = json.load(open('results/stage_b/stage_b_results.json'))
cls = json.load(open('data/neuropil_classes.json'))['classes']
out = {}
for motif in ['030T','030C','102','003']:
    gs, lab = {}, {}
    for name, entry in d['neuropils'].items():
        if name not in cls: continue
        z = entry['z_dp'][motif]
        if not np.isfinite(z) or abs(z) > 1e5: z = np.sign(z)*1e5 if np.isfinite(z) else 0.0
        gs[name] = np.array([z], dtype=float)
        lab[name] = cls[name]
    obs, p = stage_b.permutation_test_class_difference(gs, lab, n_perm=10000, seed=23)
    out[motif] = {'observed_stat': obs, 'p_value': p, 'significant_at_0.05': bool(p < 0.05)}
    print(motif, f"obs={obs:.3f} p={p:.4f}", flush=True)
res = json.load(open('results/stage_b/permutation_test.json'))
res['exploratory_single_motif_tests'] = {'note': 'POST-HOC, not pre-registered: 1-d permutation tests motivated by the stratified 030T split observed in Stage B summary.', 'tests': out}
json.dump(res, open('results/stage_b/permutation_test.json', 'w'), indent=1)
print("DONE", flush=True)
