"""Stage C single-slice trainer. Usage: train.py <start> <end> <out_dir> [data_root]
LOCKED protocol (§6): Adam lr 1e-3 batch 128, identical epoch budget (A17), identical
splits, no per-arm tuning. Refuses to run without code/stage_c/A17_FROZEN.json.
Per-run output: JSON with run_id, arm/task/sigma/seed, param count (F5), FLOP count
(F6 single fixed rule), per-epoch train/val accuracy (or MSE for T3), final metrics."""
import json, os, sys, time

def main():
    start, end, out_dir = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    data_root = sys.argv[4] if len(sys.argv) > 4 else os.path.join(out_dir, "_data")
    manifest_path = sys.argv[5] if len(sys.argv) > 5 else None
    here = os.path.dirname(__file__)
    a17_path = os.path.join(here, "A17_FROZEN.json")
    if not os.path.exists(a17_path):
        raise SystemExit("A17 mapping dictionary not frozen - training is locked (commit A17 first).")
    a17 = json.load(open(a17_path))
    sys.path.insert(0, here)
    import grid as g
    import tasks as T
    import models as M
    import torch, torch.nn as nn
    torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "2")))
    manifest = json.load(open(manifest_path or os.path.join(here, "..", "..", "results", "stage_c", "grid_manifest.json")))
    runs = manifest["runs"][start:end]
    os.makedirs(out_dir, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    for run in runs:
        if run["arm"] not in a17["applicability"].get(run["task"], a17["arms_active"]):
            continue
        out_path = os.path.join(out_dir, run["run_id"] + ".json")
        if os.path.exists(out_path):
            print(f"{run['run_id']} skip (result exists)", flush=True)
            continue
        if run["arm"] == "fly_ms_conditional" and not a17.get("fly_ms_enabled", False):
            continue
        t0 = time.time()
        tr, te, d, c = T.get_task(run, a17, data_root)
        model = M.build(run, a17, d, c, device)
        n_params = M.count_params(model)
        eff = None
        if hasattr(model, "masks"):
            eff = int(sum(int((m > 0).sum()) for m in model.masks))
        ref = a17["reference_params"][run["task"]]
        assert abs(n_params - ref) / ref <= 0.05, f"C3 violated: {run['run_id']} {n_params} vs {ref}"
        dl = torch.utils.data.DataLoader(tr, batch_size=128, shuffle=True,
                                         generator=torch.Generator().manual_seed(run["seed"]))
        dl_te = torch.utils.data.DataLoader(te, batch_size=512)
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        is_reg = run["task"] == "T3_adding"
        lossf = nn.MSELoss() if is_reg else nn.CrossEntropyLoss()
        hist = []
        for ep in range(a17["epoch_budget"][run["task"]]):
            model.train()
            for x, y in dl:
                x = x.to(device); y = y.to(device)
                opt.zero_grad(); out = model(x)
                loss = lossf(out.squeeze(), y.squeeze() if is_reg else y)
                loss.backward(); opt.step()
            model.eval(); correct = tot = 0; mse = 0.0
            with torch.no_grad():
                for x, y in dl_te:
                    x = x.to(device); y = y.to(device)
                    out = model(x)
                    if is_reg: mse += float(((out.squeeze() - y.squeeze()) ** 2).sum())
                    else:
                        correct += int((out.argmax(1) == y).sum()); tot += len(y)
            hist.append({"epoch": ep, "val_mse" if is_reg else "val_acc":
                         (mse / len(te)) if is_reg else (correct / tot)})
        ab = None
        if run.get("ablation") and hasattr(model, "masks"):
            ab = M.ablation_eval(model, dl_te, [0.0, 0.1, 0.2, 0.3, 0.4, 0.5], run["seed"], device, is_reg)
        flops = flop_count(model, d, run["task"])
        flops_eff = None
        if eff is not None and hasattr(model, "masks"):
            flops_eff = 2 * eff
        res = {"run_id": run["run_id"], "arm": run["arm"], "task": run["task"],
               "sigma": run["sigma"], "seed": run["seed"], "n_params": n_params,
               "n_params_effective": eff, "flops": flops, "flops_effective": flops_eff,
               "epochs": hist, "final": hist[-1], "ablation": ab,
               "env": {"torch": torch.__version__, "numpy": __import__("numpy").__version__},
               "elapsed_s": time.time() - t0}
        json.dump(res, open(out_path, "w"), indent=1)
        print(f"{run['run_id']} done [{time.time()-t0:.0f}s]", flush=True)

def flop_count(model, d, task):
    """F6 single fixed counting rule: 2 FLOPs per weight per forward (mul+add),
    convs counted as linear over unfolded patches. Counted on ONE forward pass shape."""
    total = 0
    for m in model.modules():
        if isinstance(m, torch.nn.Linear):
            total += 2 * m.in_features * m.out_features
        elif isinstance(m, torch.nn.Conv2d):
            side = 28 if d == 784 else 32
            oh = side // (2 ** len([x for x in model.modules() if isinstance(x, torch.nn.MaxPool2d)]))
            total += 2 * m.out_channels * (oh ** 2) * m.in_channels * m.kernel_size[0] * m.kernel_size[1]
    return total

if __name__ == "__main__":
    import torch
    main()
