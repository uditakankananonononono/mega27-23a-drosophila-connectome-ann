"""Collect Stage C run JSONs from a results directory (Drive folder or local),
validate schema + seeds against the manifest, and write git-tracked batch
checkpoints to results/stage_c/collected/. Usage: collect_results.py <results_dir> <batch_name>"""
import json, os, sys, hashlib

REQUIRED = {"run_id", "arm", "task", "sigma", "seed", "n_params", "flops", "epochs", "final", "env"}

def main():
    rdir, batch = sys.argv[1], sys.argv[2]
    manifest = json.load(open(os.path.join(os.path.dirname(__file__), "..", "..", "results", "stage_c", "grid_manifest.json")))
    by_id = {r["run_id"]: r for r in manifest["runs"]}
    got, bad = {}, []
    for fn in sorted(os.listdir(rdir)):
        if not fn.endswith(".json") or fn.startswith("_"): continue
        try:
            d = json.load(open(os.path.join(rdir, fn)))
            assert REQUIRED <= set(d), "schema"
            m = by_id[d["run_id"]]
            assert m["seed"] == d["seed"] and m["arm"] == d["arm"] and m["task"] == d["task"], "seed/arm mismatch"
            got[d["run_id"]] = d
        except Exception as e:
            bad.append((fn, str(e)))
    out = {"batch": batch, "n_valid": len(got), "n_rejected": len(bad), "rejected": bad,
           "coverage": f"{len(got)}/{manifest['n_runs']}",
           "runs_sha256": hashlib.sha256(json.dumps(sorted(got)).encode()).hexdigest(),
           "runs": got}
    od = os.path.join(os.path.dirname(__file__), "..", "..", "results", "stage_c", "collected")
    os.makedirs(od, exist_ok=True)
    json.dump(out, open(os.path.join(od, batch + ".json"), "w"), indent=1)
    print(f"valid {len(got)}/{manifest['n_runs']}, rejected {len(bad)}")

if __name__ == "__main__":
    main()
