"""B3/H2: do motif-enrichment profiles differ across neuropil functional classes?
Locked test: permutation on class labels, 10,000 permutations, p<0.05.
Statistic vector per neuropil: 16-dim z_dp profile. Class map: data/neuropil_classes.json
(committed before this test ran). Writes results/stage_b/permutation_test.json."""
import json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import stage_b

t0 = time.time()
d = json.load(open('results/stage_b/stage_b_results.json'))
cls = json.load(open('data/neuropil_classes.json'))['classes']
classes16 = ['003','012','102','021D','021U','021C','111D','111U','030T','030C','201','120D','120U','120C','210','300']
group_stats, labels = {}, {}
for name, entry in d['neuropils'].items():
    if name not in cls:
        continue
    v = np.array([entry['z_dp'][c] for c in classes16], dtype=float)
    v = np.nan_to_num(v, nan=0.0)
    v = np.clip(v, -1e6, 1e6)  # cap sd-floor artifacts so distances stay meaningful
    group_stats[name] = v
    labels[name] = cls[name]
obs, p = stage_b.permutation_test_class_difference(group_stats, labels, n_perm=10000, seed=23)
res = {'test': 'B3/H2 class-difference permutation (ANOVA-like between-minus-within on z_dp profiles)',
       'n_neuropils': len(group_stats), 'n_perm': 10000, 'seed': 23,
       'class_counts': {c: sum(1 for v in labels.values() if v == c) for c in set(labels.values())},
       'z_clipped_to': 1e6, 'observed_stat': obs, 'p_value': p,
       'significant_at_0.05': bool(p < 0.05), 'elapsed_s': time.time() - t0}
json.dump(res, open('results/stage_b/permutation_test.json', 'w'), indent=1)
print(f"obs={obs:.1f} p={p:.4f} significant={p<0.05} [{time.time()-t0:.0f}s]")
