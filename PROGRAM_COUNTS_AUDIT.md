# Gate counts audit (refreshed 2026-10-02 night), real numbers only
- Datasets/accessions: 5 (FW-001..004, LIN-001) plus derived subgraphs (78 per-neuropil, derived, not counted as external). Gate 120+. Gap about 115. Not reachable without padding.
- Executed tools: 17 ledgered (9 in the first list, 8 verified additions). Gate 40+. Gap 23. Not counted: scikit-learn, matplotlib, tqdm (no verified executed use).
- Tests: 29 test functions in 7 files.
- Formulas: 11 numbered (F1-F11) in the paper methods and results. Rich-club, FLOP count, learning speed and weighted structure are now computed in committed result files.
- Analyses completed since the last audit: rich-club (5 and 20 nulls, degree-percentile variant), threshold sweep T=1/10/50, 4-node census, ER and DP null-count sensitivity, weighted structure, FLOPs and learning speed.
- Paper: draft in paper/, 9,789 words by `cat paper/*.md | wc -w` (includes headings and markup), about 20 pages of text at 500 words/page. Gate 50+ pages of text body. Gap about 30 pages. Not padded.
- Open: N4 cell-type novelty check (route via signed-in ChatGPT in the browser first; no paid key without her per-action yes).
