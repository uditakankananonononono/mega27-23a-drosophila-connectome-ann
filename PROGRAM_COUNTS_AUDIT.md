# Gate counts audit (refreshed 2026-10-07), real numbers only
- Datasets/accessions: 6 (FW-001..004, LIN-001, ANN-001) plus derived subgraphs (78 per-neuropil, derived, not counted as external). Gate 120+. Gap about 114. Not reachable without padding.
- Executed tools: 17 ledgered (9 in the first list, 8 verified additions). Gate 40+. Gap 23. Not counted: scikit-learn, matplotlib, tqdm (no verified executed use).
- Tests: 29 test functions in 7 files.
- Formulas: 11 numbered (F1-F11) in the paper methods and results. Rich-club, FLOP count, learning speed and weighted structure are now computed in committed result files.
- Analyses completed since the last audit: N4 cell-type-pair-preserving null (20 nulls, seed 29; all 16 classes same sign as N3, emp_p at floor 0.048; Section 3.12, results/stage_a/n4_results.json).
- Paper: draft in paper/, 10,113 words by `cat paper/*.md | wc -w` (includes headings and markup), about 20 pages of text at 500 words/page. Gate 50+ pages of text body. Gap about 30 pages. Not padded. (Previous count of record 10,104; the 3.12 wording-fix commit changed it by +9.)
- Open: page-length call is hers (accept ~20 pages / fund more science / park). Times New Roman conversion held until that call lands.

## History rewrite 2026-10-07 (pre-public secret scrub)
- Before the repo returns to public, history was rewritten with git-filter-repo: (a) two WhatsApp message IDs (wamid.*, account-linked) in JUDGE_ROUNDS.md redacted across all commits and branches; (b) 4 commits authored "Instinct Agent <agent@instinct.com>" (old SHAs 74119fe, 459dfb8, 74970ab, beecb15) re-attributed to the anonymous builder identity, matching the other 264 commits.
- Every commit SHA changed. No document in the repo cited commit hashes, so no citations needed updating. Old main HEAD 91dcce8 -> rewritten HEAD noted in the push report. Content other than the redactions and attributions is unchanged; the 29-test suite passes on the rewritten history.
- This sec08 correction also landed in the same commit: the ledger's stale line saying N4 "could not obtain" annotations is updated - N4 was completed via ANN-001 (Section 3.12).
