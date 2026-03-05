#!/usr/bin/env python
# coding: utf-8
"""
ConStory-Bench Metrics: CED and GRR

Two core metrics for evaluating long-form story consistency:

1. CED (Consistency Error Density)
   - Errors per 10,000 words (normalized by story length)
   - Lower is better
   - Formula: CED = error_count / (word_count / 10000)

2. GRR (Group Relative Rank)
   - Average rank across all stories (group-relative comparison)
   - Lower is better
   - For each story, models are ranked by efficiency = word_count / (1 + error_count)
   - GRR = mean(rank_i) across all stories

Usage:
    python -m constory.metrics \
        --eval-dir output/ \
        --mode both
"""

import os
import argparse
import json
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
from tabulate import tabulate


# =============================================================================
# Evaluation Criteria (5 categories, 19 subtypes)
# =============================================================================

EVALUATION_CRITERIA = {
    "characterization": {
        "name": "Character Consistency",
        "columns": [
            "characterization_memory_contradictions",
            "characterization_knowledge_contradictions",
            "characterization_skill_power_fluctuations",
            "characterization_forgotten_abilities",
        ],
    },
    "factual_detail": {
        "name": "Factual & Detail Consistency",
        "columns": [
            "factual_detail_appearance_mismatches",
            "factual_detail_nomenclature_confusions",
            "factual_detail_quantitative_mismatches",
        ],
    },
    "narrative_style": {
        "name": "Narrative & Style",
        "columns": [
            "narrative_style_perspective_confusions",
            "narrative_style_tone_inconsistencies",
            "narrative_style_style_shifts",
        ],
    },
    "timeline_plot": {
        "name": "Timeline & Plot Logic",
        "columns": [
            "timeline_plot_absolute_time_contradictions",
            "timeline_plot_duration_timeline_contradictions",
            "timeline_plot_simultaneity_contradictions",
            "timeline_plot_causeless_effects",
            "timeline_plot_causal_logic_violations",
            "timeline_plot_abandoned_plot_elements",
        ],
    },
    "world_building": {
        "name": "World-building & Setting",
        "columns": [
            "world_building_core_rules_violations",
            "world_building_social_norms_violations",
            "world_building_geographical_contradictions",
        ],
    },
}

ALL_ERROR_COLUMNS = []
for cfg in EVALUATION_CRITERIA.values():
    ALL_ERROR_COLUMNS.extend(cfg["columns"])

TASK_TYPES = ["generation", "continuation", "expansion", "completion"]


# =============================================================================
# Helper Functions
# =============================================================================

def check_error_exists(cell_value) -> bool:
    """Check whether a cell contains at least one error (has exact_quote)."""
    if pd.isna(cell_value):
        return False
    s = str(cell_value).strip()
    if not s or s.lower() == "none":
        return False
    return "exact_quote" in s.lower()


def count_errors_in_cell(cell_value) -> int:
    """Count the number of error instances in a cell (JSON array length)."""
    if pd.isna(cell_value):
        return 0
    s = str(cell_value).strip()
    if not s or s.lower() == "none" or "exact_quote" not in s.lower():
        return 0
    try:
        arr = json.loads(s)
        if isinstance(arr, list):
            return len(arr)
    except json.JSONDecodeError:
        pass
    return 1 if "exact_quote" in s.lower() else 0


# =============================================================================
# CED: Consistency Error Density
# =============================================================================

def compute_ced_single(
    eval_path: str,
    story_column: str,
    model_name: str,
) -> Optional[Dict]:
    """
    Compute CED (Consistency Error Density) for a single model.

    Returns dict with:
        model_name, avg_density, median_density, std_density,
        avg_words, total_stories, category_densities
    """
    if not os.path.exists(eval_path):
        print(f"  [WARN] {model_name}: file not found - {eval_path}")
        return None

    try:
        df = pd.read_csv(eval_path)
    except Exception as e:
        print(f"  [ERROR] {model_name}: {e}")
        return None

    if story_column not in df.columns:
        print(f"  [WARN] {model_name}: column '{story_column}' not found")
        return None

    story_densities = []
    total_errors = 0
    total_words = 0
    cat_errors = {cat: 0 for cat in EVALUATION_CRITERIA}
    cat_words = {cat: 0 for cat in EVALUATION_CRITERIA}

    for idx in range(len(df)):
        row = df.iloc[idx]
        text = row[story_column]
        if pd.isna(text) or not isinstance(text, str):
            continue
        wc = len(text.split())
        if wc == 0:
            continue

        ec = sum(
            1
            for col in ALL_ERROR_COLUMNS
            if col in df.columns and check_error_exists(row[col])
        )

        density = ec / (wc / 10000) if wc > 0 else 0
        story_densities.append(density)
        total_errors += ec
        total_words += wc

        for cat, cfg in EVALUATION_CRITERIA.items():
            for col in cfg["columns"]:
                if col in df.columns and check_error_exists(row[col]):
                    cat_errors[cat] += 1
            cat_words[cat] += wc

    if not story_densities:
        print(f"  [WARN] {model_name}: no valid stories")
        return None

    cat_densities = {}
    for cat in EVALUATION_CRITERIA:
        if cat_words[cat] > 0:
            cat_densities[cat] = cat_errors[cat] / (cat_words[cat] / 10000)
        else:
            cat_densities[cat] = 0.0

    return {
        "model_name": model_name,
        "avg_density": np.mean(story_densities),
        "median_density": np.median(story_densities),
        "std_density": np.std(story_densities),
        "avg_words": total_words / len(story_densities),
        "avg_errors": total_errors / len(story_densities),
        "total_stories": len(story_densities),
        "category_densities": cat_densities,
    }


def compute_ced(
    model_configs: Dict[str, Tuple[str, str]],
    eval_dir: str,
    max_workers: int = 8,
) -> List[Dict]:
    """
    Compute CED for multiple models in parallel.

    Args:
        model_configs: {model_name: (eval_filename, story_column)}
        eval_dir: directory containing evaluation CSV files
        max_workers: thread pool size

    Returns:
        List of result dicts, sorted by avg_density (ascending).
    """
    print("Computing CED (Consistency Error Density)...")
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                compute_ced_single,
                os.path.join(eval_dir, fname),
                scol,
                mname,
            ): mname
            for mname, (fname, scol) in model_configs.items()
        }
        for fut in as_completed(futures):
            mname = futures[fut]
            try:
                r = fut.result()
                if r:
                    results.append(r)
                    print(
                        f"  [OK] {mname}: CED={r['avg_density']:.3f} "
                        f"({r['total_stories']} stories)"
                    )
            except Exception as e:
                print(f"  [ERROR] {mname}: {e}")

    results.sort(key=lambda x: x["avg_density"])
    return results


# =============================================================================
# GRR: Group Relative Rank
# =============================================================================

def load_model_data_for_grr(
    eval_path: str,
    story_column: str,
) -> Optional[Dict[int, Tuple[int, int]]]:
    """
    Load per-story (word_count, error_count) for GRR computation.

    Returns:
        {story_id: (word_count, error_count)}
    """
    if not os.path.exists(eval_path):
        return None

    try:
        df = pd.read_csv(eval_path)
    except Exception:
        return None

    if story_column not in df.columns or "id" not in df.columns:
        return None

    data = {}
    for idx in range(len(df)):
        row = df.iloc[idx]
        sid = row["id"]
        text = row[story_column]
        if pd.isna(text) or not isinstance(text, str):
            continue
        wc = len(text.split())
        if wc == 0:
            continue
        ec = sum(
            1
            for col in ALL_ERROR_COLUMNS
            if col in df.columns and check_error_exists(row[col])
        )
        data[sid] = (wc, ec)

    return data if data else None


def compute_grr_from_data(
    all_model_data: Dict[str, Dict[int, Tuple[int, int]]],
) -> Dict[str, float]:
    """
    Compute GRR (Group Relative Rank) across all stories.

    For each story:
        efficiency = word_count / (1 + error_count)
        rank models by efficiency (descending), lower rank = better

    GRR = mean(rank) across all stories. Lower is better.
    """
    all_ids = set()
    for sd in all_model_data.values():
        if sd is not None:
            all_ids.update(sd.keys())

    model_ranks = defaultdict(list)

    for sid in sorted(all_ids):
        group = {}
        for mn, sd in all_model_data.items():
            if sd is not None and sid in sd:
                wc, ec = sd[sid]
                group[mn] = wc / (1 + ec)

        if len(group) < 2:
            continue

        eff = pd.Series(group)
        ranks = eff.rank(ascending=False, method="min")
        for mn, r in ranks.items():
            model_ranks[mn].append(r)

    grr = {}
    for mn in all_model_data:
        if mn in model_ranks and model_ranks[mn]:
            grr[mn] = np.mean(model_ranks[mn])
        else:
            grr[mn] = np.nan
    return grr


def compute_grr(
    model_configs: Dict[str, Tuple[str, str]],
    eval_dir: str,
    max_workers: int = 8,
) -> Dict[str, float]:
    """
    Compute GRR for multiple models.

    Args:
        model_configs: {model_name: (eval_filename, story_column)}
        eval_dir: directory containing evaluation CSV files

    Returns:
        {model_name: grr_value}, sorted ascending.
    """
    print("Computing GRR (Group Relative Rank)...")

    all_data = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                load_model_data_for_grr,
                os.path.join(eval_dir, fname),
                scol,
            ): mname
            for mname, (fname, scol) in model_configs.items()
        }
        for fut in as_completed(futures):
            mname = futures[fut]
            try:
                d = fut.result()
                if d:
                    all_data[mname] = d
                    print(f"  [OK] {mname}: {len(d)} stories loaded")
                else:
                    print(f"  [WARN] {mname}: no data")
            except Exception as e:
                print(f"  [ERROR] {mname}: {e}")

    grr = compute_grr_from_data(all_data)
    return dict(sorted(grr.items(), key=lambda x: x[1]))


# =============================================================================
# Display Helpers
# =============================================================================

def print_ced_table(results: List[Dict]):
    """Print a formatted CED leaderboard table."""
    headers = [
        "Rank", "Model",
        "CED\n(Overall)",
        "Character", "Factual", "Narrative",
        "Timeline", "World",
        "Avg\nWords", "Total",
    ]
    rows = []
    for rank, r in enumerate(results, 1):
        cd = r["category_densities"]
        rows.append([
            rank, r["model_name"],
            f"{r['avg_density']:.3f}",
            f"{cd['characterization']:.3f}",
            f"{cd['factual_detail']:.3f}",
            f"{cd['narrative_style']:.3f}",
            f"{cd['timeline_plot']:.3f}",
            f"{cd['world_building']:.3f}",
            f"{r['avg_words']:,.0f}",
            r["total_stories"],
        ])
    print("\n" + "=" * 110)
    print("CED Leaderboard (Consistency Error Density per 10k words, lower is better)")
    print("=" * 110)
    print(tabulate(rows, headers=headers, tablefmt="grid",
                   stralign="center", numalign="center"))


def print_grr_table(grr: Dict[str, float], model_info: Optional[Dict] = None):
    """Print a formatted GRR leaderboard table."""
    headers = ["Rank", "Model", "GRR Overall"]
    rows = []
    for rank, (mn, val) in enumerate(grr.items(), 1):
        rows.append([rank, mn, f"{val:.2f}" if not np.isnan(val) else "N/A"])
    print("\n" + "=" * 70)
    print("GRR Leaderboard (Group Relative Rank, lower is better)")
    print("=" * 70)
    print(tabulate(rows, headers=headers, tablefmt="grid",
                   stralign="center", numalign="center"))


# =============================================================================
# CLI
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="ConStory-Bench Metrics: Compute CED and/or GRR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compute both CED and GRR
  python -m constory.metrics --eval-dir output/ --config configs/models.yaml

  # Compute CED only for a single model
  python -m constory.metrics --eval-dir output/ --mode ced \\
      --eval-file judge_gpt4o.csv --story-column generated_story --model-name gpt4o
        """,
    )
    parser.add_argument("--eval-dir", required=True, help="Evaluation CSV directory")
    parser.add_argument(
        "--mode",
        choices=["ced", "grr", "both"],
        default="both",
        help="Which metric(s) to compute",
    )
    parser.add_argument("--config", help="YAML config with model definitions")
    parser.add_argument("--eval-file", help="Single eval CSV filename")
    parser.add_argument("--story-column", help="Story column name (single model)")
    parser.add_argument("--model-name", help="Model name (single model)")
    parser.add_argument("--output", help="Output CSV path for results")
    parser.add_argument("--workers", type=int, default=8)
    return parser.parse_args()


def main():
    args = parse_args()

    # Build model configs
    if args.config:
        import yaml

        with open(args.config) as f:
            cfg = yaml.safe_load(f)
        model_configs = {
            m["name"]: (m["eval_file"], m["story_column"])
            for m in cfg["models"]
        }
    elif args.eval_file and args.story_column and args.model_name:
        model_configs = {
            args.model_name: (args.eval_file, args.story_column)
        }
    else:
        raise ValueError(
            "Provide either --config or (--eval-file, --story-column, --model-name)"
        )

    print("=" * 70)
    print("ConStory-Bench Metrics")
    print("=" * 70)
    print(f"  Eval dir:  {args.eval_dir}")
    print(f"  Mode:      {args.mode}")
    print(f"  Models:    {len(model_configs)}")
    print("=" * 70)

    if args.mode in ("ced", "both"):
        ced_results = compute_ced(
            model_configs, args.eval_dir, max_workers=args.workers
        )
        print_ced_table(ced_results)

        if args.output:
            rows = []
            for r in ced_results:
                row = {
                    "model_name": r["model_name"],
                    "ced_overall": r["avg_density"],
                    "ced_median": r["median_density"],
                    "ced_std": r["std_density"],
                    "avg_words": r["avg_words"],
                    "total_stories": r["total_stories"],
                }
                for cat, val in r["category_densities"].items():
                    row[f"ced_{cat}"] = val
                rows.append(row)
            pd.DataFrame(rows).to_csv(
                args.output.replace(".csv", "_ced.csv"),
                index=False,
                encoding="utf-8-sig",
            )

    if args.mode in ("grr", "both"):
        grr = compute_grr(
            model_configs, args.eval_dir, max_workers=args.workers
        )
        print_grr_table(grr)

        if args.output:
            rows = [
                {"model_name": mn, "grr": val}
                for mn, val in grr.items()
            ]
            pd.DataFrame(rows).to_csv(
                args.output.replace(".csv", "_grr.csv"),
                index=False,
                encoding="utf-8-sig",
            )

    print("\nDone!")


if __name__ == "__main__":
    main()
