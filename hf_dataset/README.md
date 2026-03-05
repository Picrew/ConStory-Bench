---
license: mit
task_categories:
  - text-generation
language:
  - en
  - zh
tags:
  - benchmark
  - story-generation
  - consistency
  - long-form
  - evaluation
pretty_name: ConStory-Bench
size_categories:
  - 1K<n<10K
---

<p align="center">
  <img src="assets/owl_logo.png" width="120" alt="ConStory-Bench"/>
</p>

<h1 align="center">ConStory-Bench Dataset</h1>

<p align="center">
  <b>Lost in Stories: Consistency Bugs in Long Story Generation by LLMs</b>
</p>

<p align="center">
  <a href="https://picrew.github.io/constory-bench.github.io/">Project Page</a> •
  <a href="">arXiv</a> •
  <a href="https://github.com/Picrew/ConStory-Bench">GitHub</a> •
  <a href="https://picrew.github.io/constory-bench.github.io/leadboard/">Leaderboard</a>
</p>

## What is ConStory-Bench?

A benchmark for evaluating **narrative consistency** in long-form story generation. It includes prompts across 4 task types and evaluations using an LLM-as-judge pipeline (**ConStory-Checker**) that detects contradictions with exact quotes.

<p align="center">
  <img src="assets/leaderboard.png" width="700" alt="GRR Leaderboard"/>
</p>

<p align="center">
  <img src="assets/Scatter_plot.png" width="700" alt="CED vs Average Output Length"/>
</p>

🏆 **With ConStory-Bench, we aim to track how well LLMs maintain narrative consistency as they scale. View our [Leaderboard](https://picrew.github.io/constory-bench.github.io/leadboard/) (updating).**

## Files

```text
assets/
  ├── owl_logo.png
  ├── leaderboard.png
  └── Scatter_plot.png
prompts.parquet              # Benchmark prompts
stories.parquet              # Generated stories from multiple models
evaluations/
  ├── claude_sonnet_45.csv
  ├── deepseek_r1.csv
  ├── deepseek_v3.csv
  ├── deepseek_v32_exp.csv
  ├── dome.csv
  ├── doubao.csv
  ├── gemini_25_flash.csv
  ├── gemini_25_pro.csv
  ├── glm45.csv
  ├── glm46.csv
  ├── gpt4o_1120.csv
  ├── gpt5_reasoning.csv
  ├── grok4.csv
  ├── kimi_k2_2507.csv
  ├── kimi_k2_2509.csv
  ├── ling_1t.csv
  ├── longalign_13b.csv
  ├── longwriter_zero_32b.csv
  ├── minimax_m1_80k.csv
  ├── mistral_medium_31.csv
  ├── nvidia_llama_31_ultra.csv
  ├── qwen3_235b_a22b.csv
  ├── qwen3_235b_thinking.csv
  ├── qwen3_30b_a3b_instruct_2507.csv
  ├── qwen3_32b.csv
  ├── qwen3_4b_instruct_2507.csv
  ├── qwen3_next_80b.csv
  ├── qwen3_next_80b_thinking.csv
  ├── qwenlong_l1_32b.csv
  ├── ring_1t.csv
  ├── step3.csv
  ├── superwriter.csv
  └── suri_orpo.csv
```

## Schema

### prompts.parquet

| Column | Type | Description |
| --- | --- | --- |
| `id` | int | Prompt ID (0–1999) |
| `language` | str | `en` or `zh` |
| `task_type` | str | `generation` / `continuation` / `expansion` / `completion` |
| `prompt` | str | Full prompt text |

### stories.parquet

| Column | Type | Description |
| --- | --- | --- |
| `id` | int | Prompt ID |
| `language` | str | Language |
| `task_type` | str | Task type |
| `prompt` | str | Prompt text |
| `model_name` | str | Model identifier |
| `generated_story` | str | Full generated story |
| `generation_error` | str/null | Error if generation failed |

### evaluations/*.csv

Each CSV has the story columns plus **19 error subtype columns**. Each error column contains a JSON array:

```json
[
  {
    "exact_quote": "I've never seen this woman before...",
    "location": "Chapter 5, paragraph 3",
    "contradiction_pair": "Sarah and I spent three years together...",
    "contradiction_location": "Chapter 2, paragraph 8",
    "context": "Character claims not to know someone previously described as partner"
  }
]
```

**Error columns** (5 categories, 19 subtypes):

- `characterization_memory_contradictions`, `characterization_knowledge_contradictions`, `characterization_skill_power_fluctuations`, `characterization_forgotten_abilities`
- `factual_detail_appearance_mismatches`, `factual_detail_nomenclature_confusions`, `factual_detail_quantitative_mismatches`
- `narrative_style_perspective_confusions`, `narrative_style_tone_inconsistencies`, `narrative_style_style_shifts`
- `timeline_plot_absolute_time_contradictions`, `timeline_plot_duration_timeline_contradictions`, `timeline_plot_simultaneity_contradictions`, `timeline_plot_causeless_effects`, `timeline_plot_causal_logic_violations`, `timeline_plot_abandoned_plot_elements`
- `world_building_core_rules_violations`, `world_building_social_norms_violations`, `world_building_geographical_contradictions`

## Quick Start

```python
from datasets import load_dataset
import pandas as pd

# Load prompts
prompts = load_dataset("jayden8888/ConStory-Bench", data_files="prompts.parquet", split="train")

# Load stories
stories = load_dataset("jayden8888/ConStory-Bench", data_files="stories.parquet", split="train")

# Or with pandas
prompts_df = pd.read_parquet("hf://datasets/jayden8888/ConStory-Bench/prompts.parquet")
stories_df = pd.read_parquet("hf://datasets/jayden8888/ConStory-Bench/stories.parquet")
eval_df = pd.read_csv("hf://datasets/jayden8888/ConStory-Bench/evaluations/gpt5_reasoning.csv")
```

## Evaluated Models

| Category | Models |
| --- | --- |
| Proprietary | GPT-5-Reasoning, Gemini-2.5-Pro, Gemini-2.5-Flash, Claude-Sonnet-4.5, Grok-4, GPT-4o-1120, Doubao-1.6-Thinking-2507, Mistral-Medium-3.1 |
| Open-source | GLM-4.6, Qwen3-32B, Ring-1T, DeepSeek-V3.2-Exp, Qwen3-235B-A22B-Thinking, GLM-4.5, Ling-1T, Step3, Qwen3-Next-80B-Thinking, Kimi-K2-2509, Kimi-K2-2507, Qwen3-235B-A22B, Qwen3-Next-80B, Qwen3-4B-Instruct-2507, Nvidia-Llama-3.1-Ultra, Qwen3-30B-A3B-Instruct-2507, DeepSeek-V3, QwenLong-L1-32B, DeepSeek-R1, MiniMax-M1-80k |
| Capability-enhanced | LongWriter-Zero-32B, Suri-ORPO, LongAlign-13B |
| Agent-enhanced | SuperWriter, DOME |

## Citation

```bibtex
@article{constorybench2025,
  title={Lost in Stories: Consistency Bugs in Long Story Generation by LLMs},
  author={Anonymous},
  journal={arXiv preprint arXiv:XXXX.XXXXX},
  year={2025}
}
```

## License

MIT
