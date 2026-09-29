"""Stage C task providers: fixed tasks per PREREGISTRATION §6 + A15.
Identical data splits across arms (split indices derived from seed only through
the manifest seed; train/val split itself is fixed). Noise = additive Gaussian
(T1/T2). T3 adding problem T=50. T4 permuted MNIST (permutation per seed).
T5 CIFAR-10-subset: subset definition locked in A17_FROZEN.json."""
import numpy as np

def get_task(run, a17, data_root):
    task, sigma, seed = run["task"], run["sigma"], run["seed"]
    if task in ("T1_mnist_noise", "T2_fashion", "T4_permuted_mnist"):
        import torchvision
        name = "MNIST" if task != "T2_fashion" else "FashionMNIST"
        cls = getattr(torchvision.datasets, name)
        tf = torchvision.transforms.ToTensor()
        tr = cls(data_root, train=True, download=True, transform=tf)
        te = cls(data_root, train=False, download=True, transform=tf)
        if task == "T4_permuted_mnist":
            rng = np.random.default_rng(seed)
            perm = torch_permutation(rng, 28 * 28)
            tr = Permuted(tr, perm); te = Permuted(te, perm)
        if sigma > 0:
            tr = Noisy(tr, sigma, seed); te = Noisy(te, sigma, seed + 1)
        return tr, te, 784, 10
    if task == "T3_adding":
        return Adding(5000, 50, seed), Adding(1000, 50, seed + 1), 2, 1
    if task == "T5_cifar10_subset":
        import torchvision
        tf = torchvision.transforms.Compose([torchvision.transforms.ToTensor()])
        tr = torchvision.datasets.CIFAR10(data_root, train=True, download=True, transform=tf)
        te = torchvision.datasets.CIFAR10(data_root, train=False, download=True, transform=tf)
        classes = a17["cifar10_subset_classes"]
        return SubsetClasses(tr, classes), SubsetClasses(te, classes), 3072, len(classes)
    raise ValueError(task)

def torch_permutation(rng, n):
    import torch
    return torch.tensor(rng.permutation(n), dtype=torch.long)

class Noisy:
    def __init__(self, base, sigma, seed): self.base, self.sigma, self.rng = base, sigma, np.random.default_rng(seed)
    def __len__(self): return len(self.base)
    def __getitem__(self, i):
        import torch
        x, y = self.base[i]
        return x + torch.tensor(self.rng.normal(0, self.sigma, x.shape), dtype=x.dtype), y

class Permuted:
    def __init__(self, base, perm): self.base, self.perm = base, perm
    def __len__(self): return len(self.base)
    def __getitem__(self, i):
        x, y = self.base[i]
        return x.reshape(-1)[self.perm].reshape(x.shape), y

class SubsetClasses:
    def __init__(self, base, classes):
        self.base, self.map = base, {c: k for k, c in enumerate(classes)}
        self.idxs = [i for i, (_, y) in enumerate(base) if y in self.map]
    def __len__(self): return len(self.idxs)
    def __getitem__(self, i):
        x, y = self.base[self.idxs[i]]
        return x, self.map[y]

class Adding:
    """Adding problem T=50: sequence of (value, marker) pairs; sum the two marked values."""
    def __init__(self, n, T, seed): self.n, self.T, self.rng = n, T, np.random.default_rng(seed)
    def __len__(self): return self.n
    def __getitem__(self, i):
        import torch
        rng = np.random.default_rng(int(self.rng.integers(0, 2**31)))
        vals = rng.random(self.T)
        marks = np.zeros(self.T); idx = rng.choice(self.T, 2, replace=False); marks[idx] = 1
        x = torch.tensor(np.stack([vals, marks], 1), dtype=torch.float32)
        y = torch.tensor(vals[idx].sum(), dtype=torch.float32)
        return x, y
