"""Frozen constants for the decompose-regenerate experiment.

This file is hashed into every run manifest (core.manifest). Change a value
only with a new entry in DECISIONS.md; otherwise runs made before and after the
change are silently incomparable.

Reasons for each value live in METHODS.md; the section is named beside it.
"""

# ---------------------------------------------------------------- authors
AUTHOR = "wharton"                                    # METHODS 2.2, Gate 0
AUTHOR_NAMES = {
    "austen": "Jane Austen", "cather": "Willa Cather", "chesterton": "G. K. Chesterton",
    "chopin": "Kate Chopin", "conrad": "Joseph Conrad", "joyce": "James Joyce",
    "lovecraft": "H. P. Lovecraft", "mansfield": "Katherine Mansfield",
    "melville": "Herman Melville", "sui_sin_far": "Sui Sin Far", "watanna": "Onoto Watanna",
    "wells": "H. G. Wells", "wharton": "Edith Wharton", "woolf": "Virginia Woolf",
    "mukerji": "Dhan Gopal Mukerji", "noguchi": "Yone Noguchi",
    "patrick": "Patrick Keough",        # own corpus; no A1 arm (the name means nothing to the model)
    "h_private": "Private H",  # second private corpus (2026-09-06); no A1 arm, same reason
    "patrick_v2": "Patrick Keough",     # Patrick rebuilt on the period chunker (300-800), 2026-09-06
    # contemporary published authors under Creative Commons, added 2026-09-09
    # (notes/CONTEMPORARY_AUTHORS_PLAN.md); public names, so the A1 arm stays
    "doctorow": "Cory Doctorow", "watts": "Peter Watts", "link": "Kelly Link",
    "stross": "Charles Stross", "rucker": "Rudy Rucker",
}
# the fourteen that clear 30k words; centroid population for attribution
MANIFEST_AUTHORS = ["austen", "cather", "chesterton", "chopin", "conrad", "joyce",
                    "lovecraft", "mansfield", "melville", "sui_sin_far", "watanna",
                    "wells", "wharton", "woolf"]
OTHERS_CAP = 100                                      # chunks per non-target author

# ---------------------------------------------------------------- models
BASE_MODEL = "Qwen/Qwen3-4B"                          # METHODS 6; instruct, bf16. DECISIONS G0: 3.5-4B's
                                                      # linear-attention fast path has no Windows build
                                                      # (48 s vs 5.4 s per train step measured 2026-09-03)
UPGRADE_MODEL = "Qwen/Qwen3.5-4B"                     # on disk; use if fla/causal-conv1d get installed
DECOMPOSER = "deepseek/deepseek-v4-flash-0731"        # METHODS 3.1; dated endpoint, G1: 11.6 s vs 183 s on the alias
GUIDE_MODEL = "deepseek/deepseek-v4-flash"            # METHODS 4.2; the guide was written on the alias before the switch
FRONTIER = "deepseek/deepseek-v4-flash-0731"          # F0/F5 comparator
JUDGES = ["google/gemini-3.1-flash-lite-preview", "minimax/minimax-m3"]  # METHODS 8.6; G1: gpt-5-nano spent 258 s reasoning and returned nothing
DETECTOR_PAIR = ("Qwen/Qwen3.5-9B-Base", "Qwen/Qwen3.5-9B")   # observer, performer; s5 --detect
API_BUDGET_USD = 150.0  # cumulative ledger cap (raised 110 -> 150 on 2026-09-11 09:45 after the ledger crossed 110 mid-generation; the OpenRouter balance is the real limit); 60 was crossed at 16:00 on 2026-09-09 (ledger 60.01, of which 51.7 is the 2AFC judge) and silently hung the rubric judge pass; raised with the OpenRouter balance (19.13) as the real limit

# ---------------------------------------------------------------- splits
SEED = 20260903
N_TEST = 50                                           # METHODS 2.3
N_REF_MIN = 40
TEST_WORDS = (400, 800)
VAL_WORK_FRAC = 0.10                                  # TRAIN-fit / TRAIN-val by work

# ---------------------------------------------------------------- briefs
BRIEF_MAX_TOKENS = 900
GATES = {                     # calibrated at G1, 2026-09-03; see DECISIONS.md
    "shared_ngram": 6,        # gate a: any shared word 6-gram fails (proper nouns masked)
    "ngram4_frac_max": 0.05,  # gate b (proper nouns masked)
    "len_ratio_max": 0.45,    # gate c: brief words / source words ...
    "brief_words_ok": 220,    #   ... or an absolute brief length that passes regardless
    "max_attempts": 3,        # first try + two retries
}
# gate d: words about prose. Matched on word boundaries, case-insensitive.
STYLE_WORDS = [               # narrowed at G1: only words that are about prose, never content
    "lyrical", "rhythm", "rhythmic", "cadence", "evocative", "prose", "diction",
    "imagery", "poetic", "stylistic", "pacing", "staccato", "florid", "ornate",
    "understated", "metaphor", "metaphorical", "simile", "narrative voice",
    "the writing", "writing style", "prose style", "sentence structure", "sentences",
]

# ---------------------------------------------------------------- conditioning
RETRIEVAL = {"k": 3, "max_words": 350}                # METHODS 4.1
GUIDE_N_PASSAGES = 12                                 # METHODS 4.2
GUIDE_TEMPERATURE = 0.3
GUIDE_MAX_SHARED_4GRAMS = 3                            # hard gate on quoting from the inputs

# ---------------------------------------------------------------- generation
SAMPLING = {"temperature": 0.8, "top_p": 0.95, "repetition_penalty": 1.0,
            "max_new_cap": 1500, "len_mult": 2.2}     # METHODS 6
SAMPLE_SEEDS = [0, 1]
GEN_BATCH = 4
ARMS = {
    # arm: (name, exemplars, guide, quant)
    "A0": (False, False, False, False),
    "A1": (True, False, False, False),
    "A2": (False, True, False, False),
    "A3": (False, False, True, False),
    "A4": (False, False, False, True),
    "A5": (False, True, True, True),
    "F0": (False, False, False, False),
    "F5": (False, True, True, True),
}
API_ARMS = {"F0", "F5"}
LEN_FLAG = (0.40, 2.00)                               # METHODS 6, flagged not dropped

# ---------------------------------------------------------------- training
LORA = {                                              # METHODS 7.3
    "r": 16, "alpha": 32, "dropout": 0.05,
    "targets": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "lr": 1e-4, "epochs": 3, "bs": 1, "accum": 8, "max_len": 2048,
    "warmup_ratio": 0.03, "weight_decay": 0.0,
    "eval_every": 20, "patience": 3, "views_per_target": 2, "seed": 0,
}
RECIPES = ["pair", "mix", "raw"]
CONTINUE_WORDS = (200, 400)                           # preceding-context window
INFILL_WORDS = 150

# ---------------------------------------------------------------- text normalisation
# DECISIONS 2026-09-05: Gutenberg `--` and `_italics_` were a near-perfect
# giveaway in the pilot; every scored, judged or displayed text is passed
# through core.normalise_punct. Raw-text scores are kept as scores_raw.jsonl.
NORMALISE_TEXT = True

# ---------------------------------------------------------------- outcomes
# METHODS 8.3. SHOWN: written into the A4/A5 prompt, scored only for compliance.
SHOWN_FEATURES = ["sent_mean", "pct_short", "pct_long", "commas", "semi_per100",
                  "dialogue_pct", "para_mean", "open_distinct100", "dash_per100w"]
# SEALED: never shown to any model; the geometry index is computed on these.
SEALED_FEATURES = ["cr_pos", "mtld", "mattr", "template_rate", "open_entropy",
                   "open2_distinct", "staccato_anaphora", "short_run_max",
                   "distinct_3", "rep_4", "sent_echo", "delta_own"]
GEOMETRY = {"min_sep_sd": 0.20, "clip": (-1.0, 2.0), "overshoot": 1.25}
MEMO = {"lcs_words": 12, "ngram": 8}                  # METHODS 8.5
PRIMARY = "luar_cos_source"
SECONDARY = ["geo_index", "luar_attrib", "delta_rank", "judge_fool_source", "detect_auroc"]
