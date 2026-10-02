# 2. Data and Methods

## 2.1 Connectome data
We analyzed the FlyWire FAFB v783 proofread whole-brain connectome (Dorkenwald et al., 2024; Zenodo record 10.5281/zenodo.10676866). Four release files were downloaded and verified against the published MD5 checksums: the proofread root-ID list (139,255 neurons), the pre- and post-synaptic per-neuron neuropil count tables, and the proofread connection table (258 batches, about 50 million neuron-neuron-neuropil rows with six per-connection neurotransmitter prediction averages). A comparison archive of v630-snapshot network analyses (Lin et al., 2024; Zenodo 12572930) was used only for cross-checking, never as an input.

## 2.2 Graph definition
Nodes are proofread neurons. A directed edge i to j exists when the total synapse count from i to j, summed over neuropils, is at least 5, the standard strong-connection threshold of the FlyWire consortium. This yields 2,700,513 directed edges over 134,181 neurons. The threshold was fixed in the preregistration before any analysis.

## 2.3 Motif census and null models
Directed triads were classified in the 16 standard triad classes (003 to 300) by an exact census; a brute-force NetworkX reference verified the fast census on test graphs. Three null models were used, each answering a different question.

- N1: degree-preserving directed randomization by edge swaps (10 successful swaps per edge, simple and loopless result, seeded).
- N2: matched-density directed Erdos-Renyi graphs.
- N3: a compartment-preserving randomization implemented in C (dp_rewire_c), which keeps each edge's endpoint neuropil assignment. N3 asks whether an enrichment survives once coarse anatomical organization is held fixed.

For each class c, the enrichment z-score is

(F1)  z_c = (O_c - mu_c) / sigma_c,

where O_c is the observed count and mu_c, sigma_c are the null mean and standard deviation. Empirical p-values were corrected by Benjamini-Hochberg false discovery control at q = 0.05 across all classes. A class is called Tier-1 confirmatory only if it is significant under N1, N2 and N3.

Convergence of the swap chain was checked explicitly on 3 chains at the longer 40-epoch setting. Eight classes with small counts did not converge under that criterion (111D, 111U, 120C, 120D, 120U, 201, 210, 300). Their z-scores are reported as context and never as headline findings.

## 2.4 Reciprocity, modularity and rich-club
Reciprocity is the fraction of edges whose reverse edge is also present:

(F2)  r = |{(i,j) in E : (j,i) in E}| / |E|.

Modularity is the Louvain objective on the unweighted undirected simplification,

(F3)  Q = (1/2m) sum_ij [A_ij - k_i k_j / 2m] delta(c_i, c_j),

maximized over 25 seeded restarts. Community stability was quantified by pairwise variation of information.

The rich-club coefficient at degree k is

(F4)  phi(k) = 2 E_{>k} / (N_{>k} (N_{>k} - 1)),

computed on the undirected simple projection with total-degree thresholds, and normalized by the mean over 5 degree-preserving null graphs,

(F5)  rho(k) = phi(k) / <phi_null(k)>.

## 2.5 Neuropil stratification
Each neuron was assigned to the neuropil holding the largest share of its pre- plus post-synaptic counts (ties broken by pre count). An independent streaming recomputation matched on all 134,181 neurons with zero mismatches in neuropil or count. Induced subgraphs of the 51 neuropils with at least 200 neurons were tested with the same nulls. The hypothesis that enrichment profiles differ across sensory, associative and motor neuropil classes was tested by a 10,000-permutation test on class labels.

## 2.6 Neurotransmitter-associated structure
Each edge was labeled with its dominant predicted neurotransmitter (argmax of the six averages). These are model predictions. We make no claim about functional excitation or inhibition.

## 2.7 Reproducibility
All thresholds, nulls and tests were fixed in a version-locked preregistration, hashed in the first commit of the repository. Later changes ship as dated amendments. Git history is the provenance record, and every number in this paper is read from a committed results file.
