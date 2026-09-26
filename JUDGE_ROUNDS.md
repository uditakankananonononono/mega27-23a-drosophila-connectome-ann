# JUDGE ROUNDS — mega27-23a (From Connectome to Computation)

Program rule: minimum 10 ChatGPT rounds per project on weaknesses + concrete improvements (user WhatsApp 4:11:18, verified). Mechanism: cloud browser on the user's ChatGPT account. Judges critique design/presentation/completeness/controls; they NEVER redefine locked gates after outcomes (AMENDMENT-1).

---

## ROUND 1 — 2026-09-26 ~4:13 PM IST — Design critique (pre-results)

### PROMPT (verbatim)
You are an ISEF-level science fair judge and computational neuroscientist. Critique this research project DESIGN (no results yet - it is pre-registered). Be harsh and specific.

PROJECT: "From Connectome to Computation" - mining the Drosophila FlyWire connectome (FAFB v783: 139,255 proofread neurons, 2.7M directed edges at >=5 synapses) for architectural principles that transfer to artificial neural networks.

STAGE A: directed 3-node motif census (16 classes) + reciprocity + rich-club + Louvain modularity + excitation/inhibition organization (from per-edge neurotransmitter predictions) vs TWO null families: 100 degree-preserving rewired graphs + 100 matched-density Erdos-Renyi. Enrichment declared only if significant under BOTH nulls at BH FDR q=0.05.

STAGE B: per-neuropil (brain region) stratified motif enrichment (78 regions, min 200 neurons each), permutation test for enrichment-profile differences across sensory/associative/motor region classes. Output: ranked list of candidate computational structures.

STAGE C: translate top enriched structures into ANN wiring rules. Architectures: dense MLP baseline, random-sparse MLP (matched density), fly-derived network, fly-derived + signed E/I weights. Parameter count matched within 5%.

STAGE D: controlled experiments on noisy MNIST, Fashion-MNIST, sequence prediction (adding problem), permuted-MNIST learning-speed probe. Gates: (G1) fly-derived beats random-sparse on noise-robustness AUC, (G2) shallower accuracy-degradation slope under random neuron ablation 0-50%, (G3) better accuracy-per-parameter or accuracy-per-FLOP than dense at matched budget. >=10 seeds, Wilcoxon p<0.05.

QUESTIONS:
1. What are the weakest points of this design?
2. What is missing that would make it genuinely novel and ISEF-competitive rather than a solid but routine replication of network-motif analysis?
3. What specific additions (analyses, controls, experiments, comparisons) would most raise its scientific value?
Number your answers and be concrete.

### RESPONSE (verbatim, full page capture; intermediate assistant turn included)
judge and computational neuroscientist. Critique this research project DESIGN (no results yet - it is pre-registered). Be harsh and specific.

Please paste the full pre-registered research design (title, abstract, hypothesis, datasets, methods, models, evaluation plan, controls, and claimed novelty). I’ll critique it as an ISEF judge, not as a collaborator.

I’ll specifically evaluate:

Scientific question

Is the hypothesis falsifiable?

Is the biological/computational question meaningful?

Is the scope appropriate for a student project versus a PhD-level program?

Novelty

Is this genuinely new, or a repackaging of existing methods?

Does the proposed contribution come from the biology, algorithm, dataset, or just model complexity?

Data validity

Are datasets appropriate and sufficiently powered?

Are labels reliable?

Are there hidden leakage/confounding problems?

Is the proposed inference stronger than the data can support?

Computational methodology

Whether the ML architecture is justified or “AI decoration”

Whether baselines are adequate

Whether ablations are planned

Whether the model complexity matches the data size

Statistical rigor

Proper train/test separation

Multiple testing correction

External validation

Effect sizes versus p-values

Reproducibility

ISEF judging criteria

Research question (clarity and significance)

Design and methodology

Execution feasibility

Creativity/potential impact

Understanding of limitations

Likely judge objections

“This is just correlation”

“The model predicts because of dataset artifacts”

“The biology claim exceeds the computational evidence”

“A neural network was unnecessary”

“The student cannot realistically validate this claim”

I’ll give:

Overall score estimate (ISEF-style)

Fatal flaws (if any)

Major weaknesses

Strengths worth preserving

Specific redesign suggestions

Whether it is competitive at local/state/ISEF level

Send the design. I’ll wait until I have the actual proposal before judging.

You are an ISEF-level science fair judge and computational neuroscientist. Critique this research project DESIGN (no results yet - it is pre-registered). Be harsh and specific.PROJECT: "From Connectome to Computation" - mining the Drosophila FlyWire connectome (FAFB v783: 139,255 proofread neurons, 2.7M directed edges at >=5 synapses) for architectural principles that transfer to artificial neural networks.STAGE A: directed 3-node motif census (16 classes) + reciprocity + rich-club + Louvain modularity + excitation/inhibition organization (from per-edge neurotransmitter predictions) vs TWO null families: 100 degree-preserving rewired graphs + 100 matched-density Erdos-Renyi. Enrichment declared only if significant under BOTH nulls at BH FDR q=0.05.
Show more
ISEF Judge Review — Pre-registered Design Critique

Project: “From Connectome to Computation”
Stage A: FlyWire Drosophila connectome motif/topology mining → architectural principles for artificial neural networks

Overall impression (before results)

This is a scientifically serious computational neuroscience project, substantially above the typical high-school ML project. The choice of FlyWire is excellent: a near-complete connectome is a rare resource, and the use of graph null models shows awareness that “interesting-looking network structure” is meaningless without comparison.

However, the current design has a major conceptual gap:

You are measuring properties of a biological wiring diagram and implicitly moving toward claims about computational principles, but Stage A only establishes that the fly connectome is non-random—not that the discovered structures compute anything useful or transfer to artificial neural networks.

That distinction will be the central judge criticism.

My preliminary ISEF-style assessment:

Criterion	Assessment
Question significance	Very high
Dataset choice	Excellent
Computational rigor	Good
Biological interpretation	Moderate risk
AI transfer claim	Currently unsupported
ISEF competitiveness	Potentially strong, but depends entirely on later stages
1. Scientific question critique
Current implied question:

“What architectural principles in the fly connectome could inspire artificial neural networks?”

This is too broad.

The connectome can answer:

“Which graph structures are statistically overrepresented in the Drosophila nervous system?”

It cannot directly answer:

“Which structures improve artificial computation?”

Those require a second experimental system.

A skeptical judge will ask:

“You found motif X is enriched. Why should an ANN using motif X perform better? What computational problem does motif X solve?”

Right now, Stage A risks becoming connectomics archaeology rather than computational neuroscience.

2. Motif census: strong idea, but common trap
Strength:

The 16 directed 3-node motifs are a reasonable starting point.

Comparing:

empirical connectome

degree-preserving rewires

Erdős–Rényi matched density

is much better than simply saying:

“The brain contains more triangles than random networks.”

Good.

Major issue: degree-preserving nulls may not be enough

A degree-preserving shuffle preserves:

in-degree

out-degree

But biological networks have additional constraints:

spatial embedding

cell type

developmental lineage

synaptic distance

neurotransmitter identity

hierarchy

neuron class connectivity

A motif could appear enriched simply because neurons are spatially organized.

Example:

Photoreceptors → lamina → medulla neurons naturally create feedforward motifs.

A degree shuffle destroys biological organization, making enrichment almost guaranteed.

A stronger null family would include:

Null 3: spatially constrained rewiring

Preserve:

source neuron location

target neuron location distribution

connection distance

Otherwise judges may say:

“Your null model is too biologically naive.”

3. 100 rewired graphs: probably insufficient

This is a statistical weakness.

For a 139,255-node graph:

100 null graphs sounds large, but for rare motifs it may not be.

Suppose your motif appears in:

real graph: 8,000 occurrences

null mean: 7,850

null SD: 60

Fine.

But if:

real: 320

null mean: 250

null SD: 30

your p-value estimate becomes unstable.

For extreme tails, I would expect:

≥1,000 null samples for key claims

or use analytical/randomization approaches.

A judge may ask:

“Why 100? Was this chosen before seeing results?”

Because this is preregistered, you need a justification.

4. BH FDR q=0.05: good but incomplete

This is one of the stronger parts.

You correctly recognize:

many motifs tested

multiple comparisons problem

However:

You have several analysis families:

motif enrichment

reciprocity

rich-club

modularity

E/I organization

Are you applying BH:

Option A:

separately within each family?

or

Option B:

across all tests?

This matters.

A skeptical statistician will ask:

“How did you define the hypothesis universe before seeing the data?”

Pre-registration helps, but your multiple testing plan needs to be explicit.

5. Neurotransmitter prediction problem

This is potentially your biggest biological weakness.

You say:

“excitation/inhibition organization from per-edge neurotransmitter predictions”

Important question:

Are these experimentally validated?

Because predicted neurotransmitters are not equivalent to measured physiology.

Problems:

prediction uncertainty

classifier bias

incomplete ground truth

false confidence

If a neurotransmitter prediction model says:

neuron A is cholinergic

that is not the same as:

neuron A functionally excites neuron B in vivo.

Your language must be careful.

Do not write:

“E/I organization”

Write:

“predicted neurotransmitter-associated connectivity organization”

unless validated.

6. Rich-club analysis

Potentially interesting, but be careful.

Rich-club coefficients are very sensitive to:

degree distribution

network density

threshold choice

Questions judges will ask:

What defines a “hub”?

Is the threshold preregistered?

Are you comparing against degree-preserving networks?

Are hubs biologically meaningful cell types?

A graph-theoretic rich club is not automatically a computational mechanism.

7. Louvain modularity: weak point

I would be cautious here.

Louvain is extremely common.

Finding modules in connectomes is not novel.

Potential problems:

stochasticity

resolution limit

multiple partitions

You need:

multiple random seeds

stability analysis

comparison with alternative community methods

Otherwise:

“You ran Louvain and found communities”

is not an ISEF-level contribution.

8. Biggest conceptual flaw: no computational test

This is the elephant in the room.

The title says:

From Connectome to Computation

But Stage A only does:

Graph → statistics

No computation.

To justify the title, later stages need something like:

Example:

Take enriched motif:

feedforward inhibitory motif

Construct ANN variants:

Baseline:

MLP

Experimental:

MLP + biological motif constraint

Compare:

accuracy

parameter efficiency

robustness

learning speed

generalization

Then you can say:

“This biological architectural principle improves artificial computation.”

Without that:

Your conclusion becomes:

“The fly brain is organized.”

That is already known.

9. Novelty assessment
What is genuinely good:

Large-scale FlyWire analysis

rigorous null models

preregistration

attempt to bridge neuroscience and AI

What is not novel alone:

motif counting

Louvain communities

rich-club analysis

connectome graph statistics

Thousands of papers have done related analyses.

The novelty must come from:

finding a principle + demonstrating computational advantage.

10. Likely ISEF judge questions

You should be able to answer these:

Q1:

“Why should a motif enriched in evolution be useful in an ANN?”

Current answer:
❌ unknown

Needed:
A computational hypothesis.

Q2:

“How do you know enrichment is not caused by anatomy?”

Current answer:
⚠️ insufficient

Needed:
spatial null model.

Q3:

“Why Drosophila?”

Good answer:

complete connectome availability

cellular resolution

experimentally tractable

Bad answer:

“because it is like the human brain”

Do not claim that.

Q4:

“What biological function does motif X implement?”

Need:

literature connection

known circuits

predicted computational role

Score as currently designed
ISEF potential:

7.5/10

Very good foundation.

If Stage B validates ANN transfer:

9+/10 potential

If it ends after Stage A:

Probably:

Regeneron-level science fair finalist potential: unlikely

because it demonstrates sophisticated analysis but not a new scientific discovery.

Three changes I would require before considering this ISEF-winning caliber
1. Add a computational hypothesis

Example:

“Specific overrepresented inhibitory motifs improve robustness to noisy inputs when incorporated into neural architectures.”

Now you can test something.

2. Add biological null models

At minimum:

degree-preserving

density-preserving

spatially constrained

3. Force every graph discovery to produce a computational experiment

Pipeline:

FlyWire discovery
        ↓
candidate architecture
        ↓
ANN implementation
        ↓
benchmark task
        ↓
ablation
        ↓
mechanistic interpretation

That transforms this from:

“connectome descriptive analysis”

into:

“bio-inspired AI architecture discovery.”

Final judge verdict

The project design is sophisticated and credible, but Stage A alone is not enough for the title it claims. The danger is producing a beautiful atlas of graph statistics without demonstrating that the brain’s architecture contains transferable computational principles.

The deciding factor will be whether the project moves from:

“What structures exist?”

to:

“Why did evolution favor these structures, and can they improve computation?”

### CRITIQUE -> CHANGE MAPPING (builder response)
1. "Non-random is not computationally useful; force every graph discovery into a computational experiment" -> ACCEPTED: Stage C now requires an explicit per-motif computational hypothesis per candidate structure (AMENDMENT-2 item A2). This was the locked intent of Stage C/D; made explicit per-motif.
2. "Add spatially/biologically constrained null; degree shuffle makes enrichment almost guaranteed" -> ACCEPTED as N3: region-preserving null (preserve in/out degree AND primary-neuropil of both endpoints) as a third null family, applied to whole-brain rerun and Stage B (AMENDMENT-2 item A1). True spatial-coordinate null is impossible with the current data products (no soma coordinates in v783 static release); region-preserving is the honest proxy and is documented as such.
3. "100 nulls may be too few for rare motifs" -> PARTIALLY ACCEPTED: locked N=100 stands for the primary claim (pre-registered); an extended-null sensitivity arm (1000 ER + as many DP as compute allows) is added as a sensitivity check, reported separately (AMENDMENT-2 item A3).
4. "Define the BH hypothesis universe explicitly" -> ACCEPTED: BH applied across the 16 motif classes within the whole-brain family; Stage B per-neuropil tests form their own family; other statistics (reciprocity, rich-club, modularity) are reported as descriptive with null comparisons, not FDR claims (AMENDMENT-2 item A4).
5. "Predicted neurotransmitters are not measured physiology" -> ACCEPTED: all language changed to "predicted-neurotransmitter-associated organization"; no functional E/I claim (AMENDMENT-2 item A5).
6. "Rich-club needs null comparison + preregistered thresholds" -> thresholds already locked (degree percentiles); ADDED rich-club curve vs DP-null curves (AMENDMENT-2 item A6).
7. "Louvain needs stability analysis" -> 25 seeded restarts already locked; ADDED partition-stability statistic (variation of information across restarts) (AMENDMENT-2 item A7).
8. "No computation in Stage A; title requires transfer experiments" -> Stage C/D are exactly that; no change beyond item 1.
