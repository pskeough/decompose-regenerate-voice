"""Shared loaders, variable dictionary and statistics helpers for analysis_2026-09-10.

Every analysis script starts with
    from lib import *          # noqa
    cells, runs, authors, briefs, refs = load_all()
and writes into OUT / <its own folder>. Nothing here touches data/ except to read it.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import textwrap
import warnings

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")
RUNS = os.path.join(DATA, "runs")
AUTHORS_DIR = os.path.join(DATA, "authors")
EVAL = os.path.join(DATA, "eval_results")
MASTER = os.path.join(DATA, "master")
OUT = os.path.join(ROOT, "results")

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

# ---------------------------------------------------------------- run naming
# legacy run ids (the first Wharton sweep and the bridge cell) that do not parse
LEGACY = {
    "base4b": ("wharton", "4b", "base", False), "base4b_r2": ("wharton", "4b", "base", True), "pair_e6_4b": ("wharton", "4b", "adapter", False),
    "chesterton_base4bc": ("chesterton", "4b", "base", True), "chesterton_paire6_4bc": ("chesterton", "4b", "adapter", True),
    "mansfield_base4b_r2": ("mansfield", "4b", "base", True), "cather_pair4b": ("cather", "4b", "adapter", False),
}
_RUN_RE = re.compile(r"^(?P<author>[a-z0-9_]+?)_(?P<kind>base|paire6|pair_e6|pair)(?P<tag>[0-9a-z_]*?)(?P<rep>_r2)?$")
PARAMS = {"17b": 1.7, "4b": 4.0, "4bc": 4.0, "8b": 8.0, "14b": 14.0, "m3b": 3.0, "m8b": 8.0, "m14b": 14.0}
AUTHOR_CLASS = {"wharton": "period", "cather": "period", "chesterton": "period", "chopin": "period", "mansfield": "period", "sui_sin_far": "period",
                "doctorow": "contemporary", "watts": "contemporary", "link": "contemporary", "stross": "contemporary", "rucker": "contemporary",
                "patrick": "private", "patrick_v2": "private", "h_private": "private"}
AUTHOR_NAME = {"wharton": "Edith Wharton", "cather": "Willa Cather", "chesterton": "G. K. Chesterton", "chopin": "Kate Chopin",
               "mansfield": "Katherine Mansfield", "sui_sin_far": "Sui Sin Far", "doctorow": "Cory Doctorow", "watts": "Peter Watts",
               "link": "Kelly Link", "stross": "Charles Stross", "rucker": "Rudy Rucker", "patrick": "Patrick (v1 chunking)",
               "patrick_v2": "Patrick", "h_private": "Private H"}
PRIVATE = {"patrick", "patrick_v2", "h_private"}
ARMS = ["A0", "A1", "A2", "A3", "A4", "A5"]
ARM_DESC = {"A0": "brief only", "A1": "brief + author name", "A2": "brief + 3 retrieved exemplars", "A3": "brief + style guide",
            "A4": "brief + quantitative style block", "A5": "brief + name + exemplars + guide + quant (everything)"}


def parse_run(name):
    """-> dict(author, tag, kind, replicate, family, params_b) or None."""
    if name in LEGACY:
        au, tag, kind, rep = LEGACY[name]
    else:
        m = _RUN_RE.match(name)
        if not m:
            return None
        au, tag, kind, rep = m.group("author"), (m.group("tag") or "").strip("_") or "4b", ("base" if m.group("kind") == "base" else "adapter"), bool(m.group("rep"))
    if au not in AUTHOR_CLASS or tag not in PARAMS:
        return None
    fam = "Ministral3" if tag.startswith("m") else "Qwen3"
    return {"run": name, "author": au, "tag": tag, "kind": kind, "replicate": rep, "family": fam, "params_b": PARAMS[tag],
            "size_key": f"{fam}-{PARAMS[tag]:g}B"}


# ---------------------------------------------------------------- variable dictionary
# name: (label, construct, source, direction, order_sensitive, note)
# construct: voice_embed | voice_structure | construction | adherence | tell | length | attribution | meta
# direction: '+' higher = closer to the author / better; '-' higher = worse; '0' descriptive
VARIABLES = {
    "luar_cos_source": ("LUAR cosine to the source passage", "voice_embed", "scores.jsonl", "+", False, "primary in the pre-registration; content-inflated (same brief), see luar_cos_ref"),
    "luar_cos_ref": ("LUAR cosine to the author's reference set", "voice_embed", "scores.jsonl", "+", False, "content-free voice anchor"),
    "luar_cos_ai": ("LUAR cosine to generic AI prose", "voice_embed", "scores.jsonl", "-", False, ""),
    "luar_attrib": ("LUAR attribution: author ranked first among reference authors", "attribution", "scores.jsonl", "+", False, "1/0 per passage"),
    "luar_nearest": ("LUAR nearest reference author", "attribution", "scores.jsonl", "0", False, "categorical"),
    "wegmann_cos_source": ("Wegmann style-embedding cosine to the source", "voice_embed", "scores.jsonl", "+", False, "content-independent style embedding"),
    "wegmann_cos_ref": ("Wegmann cosine to the author's reference set", "voice_embed", "scores.jsonl", "+", False, ""),
    "wegmann_cos_ai": ("Wegmann cosine to generic AI prose", "voice_embed", "scores.jsonl", "-", False, ""),
    "wegmann_attrib": ("Wegmann attribution: author ranked first", "attribution", "scores.jsonl", "+", False, ""),
    "styledist_cos_source": ("StyleDistance cosine to the source", "voice_embed", "scores.jsonl", "+", False, ""),
    "styledist_cos_ref": ("StyleDistance cosine to the reference set", "voice_embed", "scores.jsonl", "+", False, ""),
    "styledist_cos_ai": ("StyleDistance cosine to generic AI prose", "voice_embed", "scores.jsonl", "-", False, ""),
    "styledist_attrib": ("StyleDistance attribution: author ranked first", "attribution", "scores.jsonl", "+", False, ""),
    "geo_index": ("Sealed geometry index: position on the author-versus-AI feature axis (authors' own passages about 0.92, other authors 0.83, bare 4B generations 0.14)", "voice_structure", "scores.jsonl", "+", True, "higher = closer to the author (direction corrected 2026-09-10 from the data); coherence rows never enter it"),
    "delta_own": ("Burrows Delta to the author's own profile", "voice_structure", "scores.jsonl", "-", False, ""),
    "delta_nearest": ("Burrows Delta to the nearest other author", "attribution", "scores.jsonl", "0", False, ""),
    "delta_rank": ("Burrows Delta rank of the author among references", "attribution", "scores.jsonl", "-", False, "1 = author is nearest"),
    "cr_pos": ("Clause-rhythm position (order-sensitive)", "voice_structure", "scores.jsonl", "0", True, "qualified at AUC 0.87-1.00; direction author-specific, use distance to the author's reference"),
    "open_entropy": ("Entropy of sentence-opener distribution", "voice_structure", "scores.jsonl", "0", True, "opener monotony instrument; AUC 0.82-1.00"),
    "open_top_share": ("Share of sentences starting with the most common opener", "voice_structure", "scores.jsonl", "-", True, ""),
    "open_distinct": ("Distinct sentence openers / sentences", "voice_structure", "scores.jsonl", "0", True, ""),
    "open2_distinct": ("Distinct two-word openers / sentences", "voice_structure", "scores.jsonl", "0", True, ""),
    "pct_short8": ("Share of sentences of eight words or fewer", "voice_structure", "scores.jsonl", "0", True, "the one measure ordering all five blind grades on 2026-08-15"),
    "sent_len_mean": ("Mean sentence length (words)", "voice_structure", "scores.jsonl", "0", False, ""),
    "sent_len_cv": ("Coefficient of variation of sentence length", "voice_structure", "scores.jsonl", "0", False, ""),
    "short_run_max": ("Longest run of consecutive short sentences", "voice_structure", "scores.jsonl", "-", True, ""),
    "staccato_anaphora": ("Anaphoric short-sentence runs", "tell", "scores.jsonl", "-", True, ""),
    "template_rate": ("Rate of templated constructions", "tell", "scores.jsonl", "-", True, ""),
    "mattr": ("Moving-average type-token ratio (window 50)", "voice_structure", "scores.jsonl", "0", False, "lexical diversity; adapters narrow it"),
    "mtld": ("Measure of textual lexical diversity", "voice_structure", "scores.jsonl", "0", False, ""),
    "distinct_3": ("Distinct trigram ratio", "construction", "scores.jsonl", "+", False, "length-contaminated (rho with words -0.44)"),
    "rep_4": ("Repeated 4-gram rate", "construction", "scores.jsonl", "-", False, "length-contaminated"),
    "sent_echo": ("Sentence echo: near-duplicate sentence share", "construction", "scores.jsonl", "-", True, "uncapped degeneracy row; PER (600-word cap) is the primary coherence row"),
    "max_repeat": ("Longest repeated span", "construction", "scores.jsonl", "-", False, ""),
    "memo_8gram": ("8-gram overlap with the author's training text", "tell", "scores.jsonl", "-", False, "copying / memorisation"),
    "memo_lcs": ("Longest common substring with training text", "tell", "scores.jsonl", "-", False, ""),
    "memo_flag": ("Memorisation flag", "tell", "scores.jsonl", "-", False, ""),
    "commas_per_sent": ("Commas per sentence", "voice_structure", "scores.jsonl", "0", False, ""),
    "em_dashes_per_100w": ("Em dashes per 100 words", "voice_structure", "scores.jsonl", "0", False, "glyph fold applied in eval measures"),
    "words": ("Generated words", "length", "scores.jsonl", "0", False, ""),
    "len_ratio": ("Generated / target word ratio", "length", "scores.jsonl", "0", False, ""),
    "n_sent": ("Sentence count", "length", "scores.jsonl", "0", False, ""),
    "truncated": ("Hit the token cap", "length", "gens flags", "-", False, "gate: <= 20% per run on Qwen; reported not gated on Ministral"),
    "preface": ("Preface / meta text before the passage", "tell", "gens flags", "-", False, ""),
    "shown_dist": ("Distance of the passage from the shown style numbers", "adherence", "scores.jsonl", "-", False, "compliance on A4/A5 only"),
    "per": ("Proposition-echo rate (600-word cap): share of sentence pairs restating each other", "construction", "eval cache per_A0_cap600", "-", True, "S6; PASS; item-1 coherence +0.95"),
    "per_uncapped": ("Proposition-echo rate, uncapped", "construction", "eval cache per_A0", "-", True, "length-contaminated, kept for the length null"),
    "otd_js": ("Opener-class distance (sqrt JSD of fronting-class distribution vs the author's reference)", "voice_structure", "eval cache otd_A0", "-", True, "S4; PASS; ratio 13.7"),
    "para_cv_words": ("Paragraph-length coefficient of variation", "voice_structure", "eval cache psd_A0", "0", False, "S2; architecture outcome, not quality"),
    "cv_diff": ("Paragraph CV difference from the source", "voice_structure", "eval cache psd_A0", "0", False, ""),
    "w1_logpara": ("Wasserstein-1 of log paragraph lengths vs the source", "voice_structure", "eval cache psd_A0", "-", False, ""),
    "burst_an_diff": ("Corrected burstiness A_n difference from the source", "voice_structure", "eval cache cpd_A0", "0", True, "S3; PASS ratio 10.4"),
    "cpd_z": ("Cadence z-score vs the author", "voice_structure", "eval cache cpd_A0", "-", True, ""),
    "hapax_w300": ("Hapax share in 300-token windows", "voice_structure", "eval cache lexdiv_A0", "0", False, "S8; PASS; adapters narrow vocabulary"),
    "tau": ("Kendall tau-a of brief event order in the passage", "adherence", "eval cache event_order_A0", "+", True, "S7 exploratory; ceiling 0.75 on the authors' own passages"),
    "terminal_missing": ("Last brief event missing from the passage", "adherence", "eval cache event_order_A0", "-", True, "usable flag"),
    "events_present": ("Share of brief events found", "adherence", "eval cache event_order_A0", "+", True, ""),
    "arti_w": ("Constructional tell index, winsorised (AI-typical constructions per 1k words, z vs the author)", "tell", "eval cache constructional_A0", "-", True, "S5; marginal as an aggregate; per-feature table is the instrument"),
    "rfpd_w": ("Rhetorical-figure profile distance, winsorised", "voice_structure", "eval cache constructional_A0", "-", True, ""),
    "coverage": ("Brief coverage judged (share of brief items present)", "adherence", "coverage.jsonl", "+", False, "LLM judge on sample 0"),
    "fool_vs_source": ("2AFC: judge picked the generation over the author's own passage", "judge", "judge.jsonl", "+", False, "sample 0; two judges"),
    "win_vs_A0": ("2AFC: judge picked this arm over the A0 arm", "judge", "judge.jsonl", "+", False, ""),
    "rubric_C": ("Rubric construction block mean (C1-C5)", "construction", "eval_results/judge", "+", False, "shuffle-test validated; report relative to the author's calibration items"),
    "rubric_S": ("Rubric craft block mean (S1-S7)", "judge", "eval_results/judge", "+", False, "judges rank the 14B base above the private author; never absolute"),
}
CONSTRUCTS = sorted({v[1] for v in VARIABLES.values()})


def variables_table():
    rows = [{"variable": k, "label": v[0], "construct": v[1], "source": v[2], "direction": v[3], "order_sensitive": v[4], "note": v[5]} for k, v in VARIABLES.items()]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- loaders
def _read(path):
    return pd.read_parquet(path) if path.endswith(".parquet") else pd.read_csv(path)


def load_all():
    cells = _read(os.path.join(MASTER, "cells.parquet"))
    runs = _read(os.path.join(MASTER, "runs.csv"))
    authors = _read(os.path.join(MASTER, "authors.csv"))
    briefs = _read(os.path.join(MASTER, "briefs.csv"))
    refs = _read(os.path.join(MASTER, "references.parquet"))
    return cells, runs, authors, briefs, refs


def load_series():
    """Chesterton adapters trained on 25/50/100/150 briefs at Qwen3 4B (arms A0, A1); not in cells.parquet."""
    p = os.path.join(MASTER, "cells_series.parquet")
    return _read(p) if os.path.exists(p) else pd.DataFrame()


def load_frontier():
    """Frontier-model arms F0 (brief only) and F5 (full conditioning), deepseek-v4-flash, on wharton, cather, sui_sin_far."""
    p = os.path.join(MASTER, "cells_frontier.parquet")
    return _read(p) if os.path.exists(p) else pd.DataFrame()


def main_cells(cells, arms=("A0",), kinds=("base", "adapter"), replicates=False):
    d = cells[cells.arm.isin(arms) & cells.kind.isin(kinds)]
    if not replicates:
        d = d[~d.replicate]
    return d


# ---------------------------------------------------------------- statistics
def bootstrap_ci(x, stat=np.mean, n=2000, seed=0, alpha=0.05):
    x = np.asarray([v for v in x if v == v], dtype=float)
    if len(x) == 0:
        return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n, len(x)))
    boots = np.array([stat(x[i]) for i in idx])
    return (float(stat(x)), float(np.quantile(boots, alpha / 2)), float(np.quantile(boots, 1 - alpha / 2)))


def cluster_bootstrap(df, value, cluster, stat=np.mean, n=2000, seed=0):
    """Bootstrap over clusters (e.g. briefs or authors), not rows."""
    groups = [g[value].dropna().values for _, g in df.groupby(cluster)]
    groups = [g for g in groups if len(g)]
    if not groups:
        return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    point = stat(np.concatenate(groups))
    boots = []
    for _ in range(n):
        pick = rng.integers(0, len(groups), size=len(groups))
        boots.append(stat(np.concatenate([groups[i] for i in pick])))
    return (float(point), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975)))


def cohens_d(a, b):
    a = np.asarray([v for v in a if v == v], float); b = np.asarray([v for v in b if v == v], float)
    if len(a) < 2 or len(b) < 2:
        return np.nan
    s = math.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return float((a.mean() - b.mean()) / s) if s > 0 else np.nan


def cliffs_delta(a, b):
    a = np.asarray([v for v in a if v == v], float); b = np.asarray([v for v in b if v == v], float)
    if not len(a) or not len(b):
        return np.nan
    gt = sum((ai > b).sum() for ai in a); lt = sum((ai < b).sum() for ai in a)
    return float((gt - lt) / (len(a) * len(b)))


def bh_fdr(pvals):
    p = np.asarray(pvals, float)
    n = np.isfinite(p).sum()
    q = np.full_like(p, np.nan)
    order = np.argsort(np.where(np.isfinite(p), p, np.inf))
    ranked = p[order][:n]
    adj = ranked * n / (np.arange(n) + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    q[order[:n]] = np.minimum(adj, 1.0)
    return q


def spearman_ci(x, y, n=2000, seed=0):
    from scipy.stats import spearmanr
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 4:
        return (np.nan, np.nan, np.nan, np.nan, int(len(x)))
    r, p = spearmanr(x, y)
    rng = np.random.default_rng(seed)
    boots = [spearmanr(x[i], y[i])[0] for i in rng.integers(0, len(x), size=(n, len(x)))]
    return (float(r), float(np.nanquantile(boots, 0.025)), float(np.nanquantile(boots, 0.975)), float(p), int(len(x)))


def permutation_test(a, b, stat=lambda a, b: np.mean(a) - np.mean(b), n=5000, seed=0):
    a = np.asarray([v for v in a if v == v], float); b = np.asarray([v for v in b if v == v], float)
    obs = stat(a, b)
    pool = np.concatenate([a, b]); rng = np.random.default_rng(seed); k = len(a); cnt = 0
    for _ in range(n):
        rng.shuffle(pool)
        if abs(stat(pool[:k], pool[k:])) >= abs(obs):
            cnt += 1
    return float(obs), float((cnt + 1) / (n + 1))


def tost(diff, low, high, se):
    """Two one-sided tests on a difference with standard error se; returns p for equivalence."""
    from scipy.stats import norm
    p1 = 1 - norm.cdf((diff - low) / se)
    p2 = norm.cdf((diff - high) / se)
    return float(max(p1, p2))


def mixed_model(df, formula, groups="author", re_formula=None, vc=None):
    """statsmodels MixedLM wrapper; returns (result, tidy DataFrame) or (None, empty)."""
    import statsmodels.formula.api as smf
    d = df.dropna(subset=[c for c in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formula) if c in df.columns])
    if d[groups].nunique() < 3 or len(d) < 20:
        return None, pd.DataFrame()
    try:
        m = smf.mixedlm(formula, d, groups=d[groups], re_formula=re_formula, vc_formula=vc)
        # 2026-09-10: the lbfgs path returned Group Var = 0 with intercept SEs of 1e4 on these data
        # while the default optimiser converged; use the default, fall back to powell, and flag
        # a zero random-effect variance as a boundary fit rather than a result
        try:
            r = m.fit(reml=True, maxiter=300)
        except Exception:
            r = m.fit(reml=True, method="powell", maxiter=300)
    except Exception as e:  # singular fits happen with few groups; report, do not crash
        return None, pd.DataFrame([{"term": "fit_failed", "note": repr(e)[:160]}])
    ci = r.conf_int()
    tidy = pd.DataFrame({"term": r.params.index, "estimate": r.params.values, "se": r.bse.values,
                         "ci_low": ci[0].values, "ci_high": ci[1].values, "p": r.pvalues.values})
    tidy["n_obs"] = int(r.nobs); tidy["n_groups"] = int(d[groups].nunique())
    try:
        gv = float(np.asarray(r.cov_re).ravel()[0])
    except Exception:
        gv = np.nan
    tidy["group_var"] = gv
    tidy["boundary_fit"] = bool(gv == gv and gv < 1e-8)
    return r, tidy


def replicate_floor(cells, measure, arm="A0"):
    """Max |mean difference| over the twice-generated base configurations, per family."""
    out = []
    pairs = [("base4b", "base4b_r2"), ("chesterton_base4b", "chesterton_base4bc"), ("mansfield_base4b", "mansfield_base4b_r2"),
             ("chesterton_basem3b", "chesterton_basem3b_r2"), ("patrick_v2_basem3b", "patrick_v2_basem3b_r2"),
             # 2026-09-11 overnight: one replicate pair per family at 8B and 14B (chesterton), so floors are no longer borrowed across sizes
             ("chesterton_base8b", "chesterton_base8b_r2"), ("chesterton_base14b", "chesterton_base14b_r2"),
             ("chesterton_basem8b", "chesterton_basem8b_r2"), ("chesterton_basem14b", "chesterton_basem14b_r2")]
    for a, b in pairs:
        x = cells[(cells.run == a) & (cells.arm == arm)][measure].dropna(); y = cells[(cells.run == b) & (cells.arm == arm)][measure].dropna()
        if len(x) and len(y):
            fam = str(cells.loc[cells.run == a, "family"].iloc[0])   # the run's own family (was a "m3b" name test, which mislabelled the m8b/m14b pairs as Qwen3, found 2026-09-11 03:20)
            out.append({"measure": measure, "pair": f"{a} vs {b}", "family": fam, "n": min(len(x), len(y)), "abs_mean_diff": float(abs(x.mean() - y.mean()))})
    t = pd.DataFrame(out, columns=["measure", "pair", "family", "n", "abs_mean_diff"])
    for fam in ("Qwen3", "Ministral3"):
        if fam not in set(t.family):
            print(f"[lib.replicate_floor] no replicate pair scored for {fam} on {measure}; do not quote a floor for that family", file=sys.stderr)
    return t


# ---------------------------------------------------------------- output helpers
def outdir(name):
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    return d


def write_table(df, path, floats=4):
    df.to_csv(path, index=False, float_format=f"%.{floats}f")
    return path


def md_table(df, floats=3, max_rows=60):
    d = df.head(max_rows).copy()
    for c in d.columns:
        if d[c].dtype.kind == "f":
            d[c] = d[c].map(lambda v: "" if pd.isna(v) else f"{v:.{floats}f}")
    cols = list(d.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in d.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    if len(df) > max_rows:
        lines.append(f"\n({len(df) - max_rows} more rows in the csv)")
    return "\n".join(lines)


def write_readme(folder, title, what, how, reading, caveats=None, tables=None, figures=None, extra=None):
    """The written piece that accompanies every script's outputs."""
    parts = [f"# {title}", "", "## What this does", "", textwrap.dedent(what).strip(), "", "## How it does it", "", textwrap.dedent(how).strip(), ""]
    if tables:
        for name, df in tables:
            parts += [f"### {name}", "", md_table(df), ""]
    if figures:
        for name, path in figures:
            parts += [f"### {name}", "", f"![{name}]({os.path.basename(path)})", ""]
    if extra:
        parts += [textwrap.dedent(extra).strip(), ""]
    parts += ["## How to read the result, conservatively", "", textwrap.dedent(reading).strip(), ""]
    if caveats:
        parts += ["## Caveats", ""] + [f"- {c}" for c in caveats] + [""]
    open(os.path.join(folder, "README.md"), "w", encoding="utf-8", newline="\n").write("\n".join(parts))


def savefig(fig, path, dpi=150):
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path
