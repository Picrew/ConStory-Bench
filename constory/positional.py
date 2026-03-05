#!/usr/bin/env python
# coding: utf-8
"""
ConStory-Bench: Error Positional Distribution Analysis

Analyze where errors appear in stories by computing:
- Fact Position: average position (%) where the original fact is established
- Contradiction Position: average position (%) where the contradiction appears
- Gap: average |contradiction_pos - fact_pos| per error instance

Positions are normalized by story length (0-100%).

Usage:
    python -m constory.positional \
        --eval-dir evaluations/ \
        --config configs/models.yaml

    # Specific 8 representative models
    python -m constory.positional \
        --eval-dir evaluations/ \
        --config configs/models.yaml \
        --models "GPT-5-Reasoning,Claude-Sonnet-4.5,Gemini-2.5-Pro,Qwen3-235B-A22B-Thinking,GLM-4.6,DeepSeek-V3.2-Exp,Kimi-K2-2509,GPT-4o-1120"
"""

import os
import json
import argparse
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from tabulate import tabulate


# =============================================================================
# 7 Focused Error Subtypes for Positional Analysis
# =============================================================================

FOCUSED_ERROR_TYPES = {
    "timeline_plot_absolute_time_contradictions": "Absolute Time Contradictions",
    "world_building_core_rules_violations": "Core Rules Violations",
    "factual_detail_quantitative_mismatches": "Quantitative Mismatches",
    "world_building_geographical_contradictions": "Geographical Contradictions",
    "factual_detail_nomenclature_confusions": "Nomenclature Confusions",
    "characterization_memory_contradictions": "Memory Contradictions",
    "narrative_style_perspective_confusions": "Perspective Confusions",
}


# =============================================================================
# Helper Functions
# =============================================================================

def parse_error_json(cell_value) -> Optional[List[Dict]]:
    """Parse error JSON from cell value."""
    if pd.isna(cell_value):
        return None
    cell_str = str(cell_value).strip()
    if not cell_str or cell_str.lower() == "none":
        return None
    if "exact_quote" not in cell_str.lower():
        return None
    try:
        error_list = json.loads(cell_str)
        if isinstance(error_list, list) and len(error_list) > 0:
            return error_list
    except json.JSONDecodeError:
        return None
    return None


def normalize_text(text: Union[str, List, None]) -> Optional[str]:
    """Normalize text — handle both string and list inputs."""
    if text is None:
        return None
    if isinstance(text, list):
        if len(text) == 0:
            return None
        text = " ".join(str(item) for item in text if item)
    text_str = str(text).strip()
    if not text_str:
        return None
    return " ".join(text_str.split())


def find_text_position(story: str, text: Union[str, List, None]) -> Optional[float]:
    """Find the position of text in story as a percentage (0-100)."""
    if not story:
        return None
    story_normalized = normalize_text(story)
    text_normalized = normalize_text(text)
    if not story_normalized or not text_normalized:
        return None

    pos = story_normalized.find(text_normalized)
    if pos == -1:
        # Try partial match (first 50 characters)
        text_partial = text_normalized[:50] if len(text_normalized) > 50 else text_normalized
        pos = story_normalized.find(text_partial)
    if pos == -1:
        return None

    story_length = len(story_normalized)
    if story_length == 0:
        return None
    return (pos / story_length) * 100


def analyze_error_positions(
    error_list: List[Dict], story: str
) -> Dict:
    """Analyze positions of exact_quote and contradiction_pair in story."""
    exact_positions = []
    contra_positions = []
    gaps = []

    for error in error_list:
        exact_quote = error.get("exact_quote", "")
        contra_pair = error.get("contradiction_pair", "")
        if not exact_quote or not contra_pair:
            continue

        exact_pos = find_text_position(story, exact_quote)
        contra_pos = find_text_position(story, contra_pair)

        if exact_pos is not None and contra_pos is not None:
            exact_positions.append(exact_pos)
            contra_positions.append(contra_pos)
            gaps.append(abs(contra_pos - exact_pos))

    return {
        "exact_positions": exact_positions,
        "contra_positions": contra_positions,
        "gaps": gaps,
    }


# =============================================================================
# Main Analysis
# =============================================================================

def analyze_positional_distribution(
    eval_dir: str,
    model_configs: Dict[str, Tuple[str, str]],
    selected_models: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Dict]]:
    """
    Analyze positional distribution for each model.

    Returns:
        {model_name: {error_display_name: {avg_exact_pos, avg_contra_pos, avg_gap, ...}}}
    """
    all_results = {}

    for model_name, (eval_file, story_column) in model_configs.items():
        if selected_models and model_name not in selected_models:
            continue

        path = os.path.join(eval_dir, eval_file)
        if not os.path.exists(path):
            print(f"  [WARN] {model_name}: file not found")
            continue

        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"  [ERROR] {model_name}: {e}")
            continue

        if story_column not in df.columns:
            print(f"  [WARN] {model_name}: column '{story_column}' not found")
            continue

        model_results = {}

        for col_name, display_name in FOCUSED_ERROR_TYPES.items():
            if col_name not in df.columns:
                continue

            all_exact = []
            all_contra = []
            all_gaps = []
            total_errors = 0

            for idx, row in df.iterrows():
                error_list = parse_error_json(row[col_name])
                if error_list is None:
                    continue
                total_errors += len(error_list)
                story_text = row[story_column]
                if pd.isna(story_text) or not isinstance(story_text, str):
                    continue

                positions = analyze_error_positions(error_list, story_text)
                all_exact.extend(positions["exact_positions"])
                all_contra.extend(positions["contra_positions"])
                all_gaps.extend(positions["gaps"])

            if total_errors > 0 and len(all_gaps) > 0:
                model_results[display_name] = {
                    "avg_exact_pos": np.mean(all_exact),
                    "avg_contra_pos": np.mean(all_contra),
                    "avg_gap": np.mean(all_gaps),
                    "total_errors": total_errors,
                    "extractable": len(all_gaps),
                }

        all_results[model_name] = model_results
        print(f"  [OK] {model_name}: {len(model_results)} error types analyzed")

    return all_results


def print_positional_tables(results: Dict[str, Dict[str, Dict]]):
    """Print positional distribution tables for each model."""
    error_type_names = list(FOCUSED_ERROR_TYPES.values())

    for model_name, model_results in results.items():
        print(f"\n{'='*90}")
        print(f"  {model_name}")
        print(f"{'='*90}")

        rows = []
        for et in error_type_names:
            r = model_results.get(et)
            if r is None:
                rows.append([et, "N/A", "N/A", "N/A"])
            else:
                rows.append([
                    et,
                    f"{r['avg_exact_pos']:.1f}%",
                    f"{r['avg_contra_pos']:.1f}%",
                    f"{r['avg_gap']:.1f}%",
                ])

        print(tabulate(
            rows,
            headers=["Error Type", "Fact Position", "Contradiction Position",
                     "Gap (avg|contra-fact|)"],
            tablefmt="grid",
            stralign="center",
        ))

    # Summary table across all models
    if len(results) > 1:
        print(f"\n{'='*120}")
        print("  Summary: Average across all models")
        print(f"{'='*120}")

        summary_rows = []
        for et in error_type_names:
            facts, contras, gaps = [], [], []
            for mr in results.values():
                r = mr.get(et)
                if r:
                    facts.append(r["avg_exact_pos"])
                    contras.append(r["avg_contra_pos"])
                    gaps.append(r["avg_gap"])
            if facts:
                summary_rows.append([
                    et,
                    f"{np.mean(facts):.1f}%",
                    f"{np.mean(contras):.1f}%",
                    f"{np.mean(gaps):.1f}%",
                    len(facts),
                ])
            else:
                summary_rows.append([et, "N/A", "N/A", "N/A", 0])

        print(tabulate(
            summary_rows,
            headers=["Error Type", "Avg Fact Pos", "Avg Contra Pos",
                     "Avg Gap", "Models"],
            tablefmt="grid",
            stralign="center",
        ))


# =============================================================================
# CLI
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="ConStory-Bench: Error Positional Distribution Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # All models
  python -m constory.positional --eval-dir evaluations/ --config configs/models.yaml

  # 8 representative models from paper
  python -m constory.positional --eval-dir evaluations/ --config configs/models.yaml \\
      --models "GPT-5-Reasoning,Claude-Sonnet-4.5,Gemini-2.5-Pro,Qwen3-235B-A22B-Thinking,GLM-4.6,DeepSeek-V3.2-Exp,Kimi-K2-2509,GPT-4o-1120"
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

    print("=" * 70)
    print("ConStory-Bench: Error Positional Distribution Analysis")
    print("=" * 70)
    print(f"  Eval dir: {args.eval_dir}")
    n = len(selected) if selected else len(model_configs)
    print(f"  Models:   {n}")
    print(f"  Error types: {len(FOCUSED_ERROR_TYPES)}")
    print("=" * 70)

    results = analyze_positional_distribution(
        args.eval_dir, model_configs, selected
    )
    print_positional_tables(results)

    if args.output:
        rows = []
        for mn, mr in results.items():
            for et, data in mr.items():
                rows.append({
                    "model": mn,
                    "error_type": et,
                    "fact_position": data["avg_exact_pos"],
                    "contradiction_position": data["avg_contra_pos"],
                    "gap": data["avg_gap"],
                    "total_errors": data["total_errors"],
                    "extractable": data["extractable"],
                })
        pd.DataFrame(rows).to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"\nSaved to {args.output}")

    print("\nDone!")


if __name__ == "__main__":
    main()
