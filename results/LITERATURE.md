# Prior work each analysis is read against

Citations below were cross-checked against arXiv abstract pages on 2026-09-09
(`data/docs/eval_methodology/SYNTHESIS.md`, section 6). Where a figure sits in a paper's body
rather than its abstract it is marked "body value" and must be re-read before it is quoted.

## Benchmarks of authorial emulation

- **PersonalBench** (Sawant, arXiv 2608.19746, Aug 2026): 50 authors, 1,000 generations, Qwen 3
  and GLM-4; LUAR attribution AUC 0.918; methods score 0.484-0.508 against a floor of 0.626 and
  a ceiling of 0.756, a spread of 0.024. Reads against scripts 11, 15, 18: our positions are
  reported on the same floor-to-ceiling convention, and our adapter effects should be compared
  with their 0.024 method spread.
- **Theory-grounded evaluation** (Sawant, arXiv 2604.26460, CTB Workshop ICML 2026): three metric
  traditions correlate at |r| < 0.07. Reads against script 15's correlation matrix: near-zero
  cross-tradition agreement is expected, and agreement above it is the finding.
- **Small Is Enough** (Chakravorty, arXiv 2607.29238, Jul 2026): LoRA on 0.5B-7B, composite
  plateau 0.69, AI-ness more than 20% lower; single author, LLM-judged only. Reads against
  scripts 11 and 18: a cross-size plateau is corroborated on one author with LLM judges; ours
  tests it on thirteen authors, two families and instrument measures.
- **StyloBench** (arXiv 2510.12476): fine-tuned literary imitation drops Fast-DetectGPT AUROC
  from 98.78% to 8.71%. Reads against script 21's detector table.
- **Salemi and Zamani** (arXiv 2409.09510) and **OPPU** (arXiv 2402.04401): task-accuracy
  comparisons of retrieval, PEFT and their combination in personalisation, with opposite
  rankings. Reads against script 12: the style version of the same comparison.

## Instruments

- **LUAR** and **Wegmann style embeddings**; **StyleDistance**; **STEB** (Rivera Soto, Wegmann,
  Aggazzotti, arXiv 2606.31741): 96 datasets, seven languages, no style embedding dominates.
  Reads against scripts 15 and 18: instrument disagreement per author is expected by the STEB
  authors themselves.
- **Eder 2013** and **Sun** (arXiv 2502.12150): bag-of-words measures are excellent at
  attribution. The claim tested in script 15 is not that they are broken but that they are
  validated on discrimination and read as fidelity.
- **Zamaraeva et al.** (ACL 2025, pp. 9041-9060): human text can be closer in construction
  distribution to an LLM than to another human; the population-versus-author control in the
  gates comes from here (script 15's calibration uses other authors as the floor).
- **Kim and Jo** (Phys. Rev. E 94, 032311, 2016): finite-size-corrected burstiness A_n, used by
  the cadence measure (body-value formula, re-derived in the pipeline's `cpd.py`).
- **ConStory-Bench** (Li et al., arXiv 2603.05890): consistency errors cluster mid-narrative and
  in high-entropy segments. Reads against scripts 14 and 20 (event order, terminal event).

## Judges

- **Norman et al.** (arXiv 2606.19544): 21 judges, about 541,000 judgements; kappa deflation of
  33-41 percentage points under exact match; rankings shift up to 14 positions; test-retest
  above 0.95 with position bias above 0.10. Reads against script 16: quadratic-weighted kappa
  and order effects are reported, and rankings from one judge are never quoted alone.
- **Bagaria et al.** (arXiv 2609.02942): rubric-only classifiers predict judge verdicts; judges
  fail to update under reversal (body values 0.8 and 37.7%). Reads against script 16's
  judge-versus-instrument correlations.
- **Shaib et al.** (arXiv 2509.19163): slop annotations with low agreement. Reads against the
  craft block: our inter-judge kappa on construction subscores is compared with their low
  agreement on holistic slop labels.

## What this study adds, stated so the analyses can test it

1. A protocol that holds content fixed (brief decomposition and regeneration), so voice and
   adherence are measured on the same passage separately (scripts 14, 20).
2. An adapter axis and a size axis crossed on thirteen authors and two families with a measured
   replicate floor (scripts 10, 11, 18, 19).
3. A layered instrument set with validation gates rather than a single metric (scripts 15, 22).
4. Two consented private corpora beside public ones (scripts 13, 19).
