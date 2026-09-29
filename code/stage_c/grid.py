"""Stage C run-grid generator (prep; grid is config, locked before training).
Manifest = arms x task-conditions x 20 seeds (A19: >=20 seeds; satisfies §6 >=10).
Seeds derived from SeedSequence(MASTER_SEED_C). Training REFUSES to run until
code/stage_c/A17_FROZEN.json exists (created when the A17 mapping dictionary is
committed) - enforces the locked order: A17 dictionary before any training.
Arm-task applicability and epoch budget are pinned in A17_FROZEN.json."""
import json, os
import numpy as np

MASTER_SEED_C = 26  # 23=Stage A, 24=Stage B, 25=N3, 26=Stage C
ARMS = ["base_dense", "base_sparse", "fly_m", "fly_ms_conditional",
        "ctrl_rand_sparse", "ctrl_dp_shuffled", "ctrl_er_sparse", "small_cnn", "fly_mod"]
TASKS = {"T1_mnist_noise": {"sigmas": [0.0, 0.5, 1.0, 1.5]},
         "T2_fashion": {"sigmas": [0.0, 1.0]},
         "T3_adding": {"sigmas": [0.0]},
         "T4_permuted_mnist": {"sigmas": [0.0]},
         "T5_cifar10_subset": {"sigmas": [0.0]}}
N_SEEDS = 20

def build(out_path):
    ss = np.random.SeedSequence(MASTER_SEED_C)
    runs = []
    for arm in ARMS:
        for task, spec in TASKS.items():
            for sigma in spec["sigmas"]:
                seeds = [int(s.generate_state(1)[0]) for s in ss.spawn(N_SEEDS)]
                for si, seed in enumerate(seeds):
                    runs.append({"run_id": f"{arm}|{task}|s{sigma}|k{si:02d}",
                                 "arm": arm, "task": task, "sigma": sigma,
                                 "seed_idx": si, "seed": seed})
    manifest = {"master_seed": MASTER_SEED_C, "n_seeds": N_SEEDS, "arms": ARMS,
                "tasks": {k: v["sigmas"] for k, v in TASKS.items()},
                "n_runs": len(runs), "runs": runs,
                "gate": "training blocked until code/stage_c/A17_FROZEN.json exists"}
    json.dump(manifest, open(out_path, "w"), indent=1)
    return len(runs)

if __name__ == "__main__":
    here = os.path.dirname(__file__)
    n = build(os.path.join(here, "..", "..", "results", "stage_c", "grid_manifest.json"))
    print(f"{n} runs")
