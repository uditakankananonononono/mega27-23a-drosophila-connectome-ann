"""Regression: masked arms must train without in-place autograd violations.
Bug (Sep 29 run #1, all 18 jobs exit 1): SparseMLP/FlyMLP forward mutated
lin.weight in-place under no_grad after using it -> RuntimeError version bump
on first backward. Functional masking (F.linear(x, w*m, b)) is the fix; masked
entries stay exactly zero through training (zero init + zero gradient)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code', 'stage_c'))
import torch, torch.nn as nn
import models as M

def test_masked_arms_train_without_inplace_violation():
    a17 = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'code', 'stage_c', 'A17_FROZEN.json')))
    torch.manual_seed(0)
    lossf = nn.CrossEntropyLoss()
    for name in ["base_sparse","ctrl_rand_sparse","ctrl_er_sparse","fly_m","fly_mod","ctrl_dp_shuffled","fly_ms_conditional"]:
        model = M.build({"arm":name,"seed":123,"run_id":"t","task":"T1_mnist_noise","sigma":0.0}, a17, 784, 10, "cpu")
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        for _ in range(4):
            x = torch.randn(16, 1, 28, 28); y = torch.randint(0, 10, (16,))
            opt.zero_grad(); loss = lossf(model(x).squeeze(), y); loss.backward(); opt.step()
        viol = sum(int(((lin.weight * (m == 0)) != 0).sum()) for lin, m in zip(model.layers, model.masks))
        assert viol == 0, f"{name}: {viol} masked entries became nonzero during training"

if __name__ == "__main__":
    test_masked_arms_train_without_inplace_violation()
    print("PASS")
