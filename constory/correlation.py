#!/usr/bin/env python
# coding: utf-8
"""
ConStory-Bench: Error Correlation Analysis

Compute conditional probability matrices P(B|A) between the 5 error
categories for each model. This answers: "Given that a story has error
category A, what is the probability it also has category B?"

Only stories with at least one error are considered.

Usage:
    python -m constory.correlation \
        --eval-dir evaluations/ \
        --config configs/models.yaml

    # Specific models only
    python -m constory.correlation \
        --eval-dir evaluations/ \
        --config configs/models.yaml \
        --models "GPT-5-Reasoning,Claude-Sonnet-4.5,Gemini-2.5-Pro"
"""

import os
import argparse
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from tabulate import tabulate


# =============================================================================
# Evaluation Criteria (5 categories)
# =============================================================================

EVALUATION_CRITERIA = {
    "timeline_plot": {
        "name": "Timeline & Plot Logic",
        "abbr": "Time.",
        "columns": [
            "timeline_plot_absolute_time_contradictions",
            "timeline_plot_duration_timeline_contradictions",
            "timeline_plot_simultaneity_contradictions",
            "timeline_plot_causeless_effects",
            "timeline_plot_causal_logic_violations",
            "timeline_plot_abandoned_plot_elements",
        ],
    },
    "characterization": {
        "name": "Character Consistency",
        "abbr": "Char.",
        "columns": [
            "characterization_memory_contradictions",
            "characterization_knowledge_contradictions",
            "characterization_skill_power_fluctuations",
            "characterization_forgotten_abilities",
        ],
    },
    "factual_detail": {
        "name": "Factual & Detail Consistency",
        "abbr": "Fact.",
        "columns": [
            "factual_detail_appearance_mismatches",
            "factual_detail_nomenclature_confusions",
            "factual_detail_quantitative_mismatches",
        ],
    },
    "narrative_style": {
        "name": "Narrative & Style",
        "abbr": "Narr.",
        "columns": [
            "narrative_style_perspective_confusions",
            "narrative_style_tone_inconsistencies",
            "narrative_style_style_shifts",
        ],
    },
    "world_building": {
        "name": "World-building & Setting",
        "abbr": "World",
        "columns": [
            "world_building_core_rules_violations",
            "world_building_social_norms_violations",
            "world_building_geographical_contradictions",
        ],
    },
}


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


def check_category_has_error(row: pd.Series, category_config: Dict) -> bool:
    """Check if a row has at least one error in a given category."""
    for col in category_config["columns"]:
        if col in row.index and check_error_exists(row[col]):
            return True
    return False


def build_binary_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert raw evaluation DataFrame to binary error matrix.
    Each row = one story, columns = 5 category abbreviations, values = 0/1.
    """
    binary = pd.DataFrame()
    for cat_config in EVALUATION_CRITERIA.values():
        abbr = cat_config["abbr"]
        binary[abbr] = df.apply(
            lambda row: 1 if check_category_has_error(row, cat_config) else 0,
            axis=1,
        )
    return binary


def compute_conditional_prob_matrix(
    binary_matrix: pd.DataFrame,
) -> Tuple[pd.DataFrame, int]:
    """
    Compute conditional probability matrix P(B|A) for 5 error categories.

    Only considers stories with at least one error.
    Row = condition A, Column = target B.

    Returns:
        (prob_df, n_stories_with_errors)
    """
    has_any = binary_matrix.sum(axis=1) > 0
    filtered = binary_matrix[has_any]
    categories = filtered.columns.tolist()
    n = len(categories)
    prob = np.zeros((n, n))

    for i, cat_a in enumerate(categories):
        rows_with_a = filtered[filtered[cat_a] == 1]
        count_a = len(rows_with_a)
        if count_a == 0:
            continue
        for j, cat_b in enumerate(categories):
            count_ab = len(rows_with_a[rows_with_a[cat_b] == 1])
            prob[i, j] = count_ab / count_a

    return pd.DataFrame(prob, index=categories, columns=categories), len(filtered)


# =============================================================================
# Main Analysis
# =============================================================================

def analyze_correlations(
    eval_dir: str,
    model_configs: Dict[str, Tuple[str, str]],
    selected_models: Optional[List[str]] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Compute error correlation matrices for each model.

    Args:
        eval_dir: directory containing evaluation CSV files
        model_configs: {model_name: (eval_filename, story_column)}
        selected_models: optional list of model names to analyze

    Returns:
        {model_name: conditional_probability_DataFrame}
    """
    results = {}

    for model_name, (eval_file, _story_col) in model_configs.items():
        if selected_models and model_name not in selected_models:
            continue

        path = os.path.join(eval_dir, eval_file)
        if not os.path.exists(path):
            print(f"  [WARN] {model_name}: file not found")
            continue

        try:
            df = pd.read_csv(path)
            binary = build_binary_matrix(df)
            prob_matrix, n_errors = compute_conditional_prob_matrix(binary)
            results[model_name] = prob_matrix
            print(
                f"  [OK] {model_name}: "
                f"{n_errors}/{len(df)} stories with ≥1 error"
            )
        except Exception as e:
            print(f"  [ERROR] {model_name}: {e}")

    return results


def print_correlation_tables(results: Dict[str, pd.DataFrame]):
    """Print correlation matrices for all models."""
    for model_name, prob_matrix in results.items():
        print(f"\n{'='*60}")
        print(f"  {model_name}")
        print(f"{'='*60}")
        # Format as table with 3 decimal places
        formatted = prob_matrix.map(lambda x: f"{x:.3f}")
        print(tabulate(
            formatted,
            headers=formatted.columns,
            showindex=True,
            tablefmt="grid",
            stralign="center",
        ))


# =============================================================================
# CLI
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="ConStory-Bench: Error Correlation Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # All models
  python -m constory.correlation --eval-dir evaluations/ --config configs/models.yaml

  # Specific models
  python -m constory.correlation --eval-dir evaluations/ --config configs/models.yaml \\
      --models "GPT-5-Reasoning,Claude-Sonnet-4.5,GLM-4.6"
        """,
    )
    parser.add_argument("--eval-dir", required=True, help="Evaluation CSV directory")
    parser.add_argument("--config", required=True, help="YAML config with model definitions")
    parser.add_argument(
        "--models",
        help="Comma-separated list of model names to analyze (default: all)",
    )
    parser.add_argument("--output", help="Output CSV path for results")
    return parser.parse_args()


def main():
    args = parse_args()

    import yaml
    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    model_configs = {
        m["name"]: (m["eval_file"], m["story_column"])
        for m in cfg["models"]
    }

    selected = None
    if args.models:
        selected = [s.strip() for s in args.models.split(",")]

    print("=" * 60)
    print("ConStory-Bench: Error Correlation Analysis")
    print("=" * 60)
    print(f"  Eval dir: {args.eval_dir}")
    n = len(selected) if selected else len(model_configs)
    print(f"  Models:   {n}")
    print("=" * 60)

    results = analyze_correlations(args.eval_dir, model_configs, selected)
    print_correlation_tables(results)

    if args.output:
        rows = []
        for mn, prob in results.items():
            for row_cat in prob.index:
                for col_cat in prob.columns:
                    rows.append({
                        "model": mn,
                        "condition": row_cat,
                        "target": col_cat,
                        "probability": prob.loc[row_cat, col_cat],
                    })
        pd.DataFrame(rows).to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"\nSaved to {args.output}")

    print("\nDone!")


if __name__ == "__main__":
    main()
