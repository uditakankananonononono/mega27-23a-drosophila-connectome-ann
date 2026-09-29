# Private-free route: job dispatch sequence (2,000 included min/month pool)

27 jobs x 60 runs, arm-major manifest (180 runs/arm = 3 jobs/arm):
jobs 0-2 base_dense | 3-5 base_sparse | 6-8 fly_m | 9-11 fly_ms_conditional |
12-14 ctrl_rand_sparse | 15-17 ctrl_dp_shuffled | 18-20 ctrl_er_sparse |
21-23 small_cnn | 24-26 fly_mod

Priority = decision-relevance (headline discovery arms + their controls first):
SEPT (<= ~1,975 min incl. 25-min phage-pilot reserve, ~18 jobs x ~105 min):
  6,7,8 (fly_m) -> 3,4,5 (base_sparse) -> 12,13,14 (ctrl_rand_sparse) ->
  15,16,17 (ctrl_dp_shuffled) -> 18,19,20 (ctrl_er_sparse) -> 24,25,26 (fly_mod)
OCT 1 (after reset): 0,1,2 (base_dense reference), 21,22,23 (small_cnn C3-exception),
  9,10,11 (fly_ms_conditional exploratory)

Dispatch string for September:
6,7,8,3,4,5,12,13,14,15,16,17,18,19,20,24,25,26

Notes:
- ~105 min/job is the weighted on-box-probe estimate (115s/run MNIST-family on 2 vCPU;
  4-vCPU runners ~2x faster; T5_cifar10_subset runs are the heavy tail). Mix variance
  exists; if Sept allotment runs short, remaining jobs slide to Oct 1 automatically
  (resume-skip makes re-dispatch safe).
- Results land on per-job branches results/job-N; merge to main after each wave so
  later dispatches skip completed runs.
- fly_ms_conditional is exploratory-only (C2 gate resolution 2026-09-29); it is
  deliberately last so it never crowds out headline arms.
