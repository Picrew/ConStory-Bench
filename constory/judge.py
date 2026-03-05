#!/usr/bin/env python
# coding: utf-8
"""
ConStory-Checker: Automated Consistency Evaluation Pipeline

Evaluates generated stories for consistency errors across 5 categories
(19 fine-grained subtypes) using any OpenAI-compatible LLM as judge.

The pipeline:
1. Loads generated stories (parquet)
2. For each story, sends 5 parallel evaluation requests (one per category)
3. Parses structured JSON responses to extract error instances
4. Saves results incrementally to CSV with resume support

Usage:
    python -m constory.judge \
        --input data/stories/gpt4o.parquet \
        --story-column generated_story \
        --model-name gpt4o \
        --judge-model gpt-4o \
        --api-base https://api.openai.com/v1 \
        --api-key $OPENAI_API_KEY \
        --concurrent 3
"""

import os
import re
import json
import asyncio
import argparse
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any

import pandas as pd
import aiohttp
from tqdm import tqdm


# =============================================================================
# Configuration
# =============================================================================

MAX_TOKENS = 10000
TEMPERATURE = 0.5
DEFAULT_CONCURRENT = 3
MAX_RETRIES = 3
RETRY_DELAY_BASE = 5
REQUEST_TIMEOUT = 600
CONNECT_TIMEOUT = 30
BATCH_DELAY_SECONDS = 1

FATAL_ERROR_CODES = {
    "Arrearage", "InvalidApiKey", "Unauthorized",
    "AccountDisabled", "InsufficientBalance",
}

# Prompt template file mapping
PROMPT_FILE_MAPPING = {
    "characterization": "characterization.md",
    "factual_detail": "factual_detail.md",
    "narrative_style": "narrative_style.md",
    "timeline_plot": "timeline_plot.md",
    "world_building": "world_building.md",
}

# Evaluation criteria taxonomy (5 categories, 19 subtypes)
EVALUATION_CRITERIA = {
    "characterization": {
        "name": "Character Consistency",
        "sub_criteria": [
            "memory_contradictions",
            "knowledge_contradictions",
            "skill_power_fluctuations",
            "forgotten_abilities",
        ],
    },
    "factual_detail": {
        "name": "Factual & Detail Consistency",
        "sub_criteria": [
            "appearance_mismatches",
            "nomenclature_confusions",
            "quantitative_mismatches",
        ],
    },
    "narrative_style": {
        "name": "Narrative & Style",
        "sub_criteria": [
            "perspective_confusions",
            "tone_inconsistencies",
            "style_shifts",
        ],
    },
    "timeline_plot": {
        "name": "Timeline & Plot Logic",
        "sub_criteria": [
            "absolute_time_contradictions",
            "duration_timeline_contradictions",
            "simultaneity_contradictions",
            "causeless_effects",
            "causal_logic_violations",
            "abandoned_plot_elements",
        ],
    },
    "world_building": {
        "name": "World-building & Setting",
        "sub_criteria": [
            "core_rules_violations",
            "social_norms_violations",
            "geographical_contradictions",
        ],
    },
}


class FatalAPIError(Exception):
    """Raised when an unrecoverable API error is detected."""
    pass


# =============================================================================
# Logging
# =============================================================================

def setup_logger(name: str, log_file: str, level: str = "INFO") -> logging.Logger:
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    logger.handlers.clear()

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


# =============================================================================
# Prompt Loader
# =============================================================================

def load_prompt_templates(prompts_dir: str) -> Dict[str, str]:
    """Load evaluation prompt templates from the prompts directory."""
    templates = {}
    for criteria, filename in PROMPT_FILE_MAPPING.items():
        filepath = os.path.join(prompts_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Prompt template not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            templates[criteria] = f.read()
    return templates


# =============================================================================
# OpenAI-Compatible Judge Client
# =============================================================================

class JudgeLLMClient:
    """Async LLM client for consistency evaluation via OpenAI-compatible API."""

    def __init__(
        self,
        api_base: str,
        api_key: str,
        model: str,
        max_concurrent: int,
        logger: logging.Logger,
    ):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = logger

    async def evaluate_criteria(
        self,
        session: aiohttp.ClientSession,
        prompt_template: str,
        story_content: str,
        criteria_name: str,
    ) -> Dict[str, Any]:
        """Evaluate a story for one criteria category with retry logic."""
        async with self.semaphore:
            prompt = prompt_template.replace("{{ Content }}", story_content)
            prompt = prompt.replace(
                "{{ Query }}",
                f"{EVALUATION_CRITERIA[criteria_name]['name']} Analysis",
            )

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "stream": False,
            }
            timeout = aiohttp.ClientTimeout(
                total=REQUEST_TIMEOUT, connect=CONNECT_TIMEOUT
            )

            for retry in range(MAX_RETRIES):
                try:
                    url = f"{self.api_base}/chat/completions"
                    async with session.post(
                        url, json=payload, headers=headers, timeout=timeout
                    ) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            msg = result["choices"][0]["message"]
                            content = msg.get("content", "")
                            return {"success": True, "content": content}
                        else:
                            error_text = await resp.text()
                            self.logger.warning(
                                f"[{criteria_name}] API error "
                                f"(retry {retry+1}/{MAX_RETRIES}): "
                                f"HTTP {resp.status}"
                            )
                            try:
                                ej = json.loads(error_text)
                                code = ej.get("error", {}).get("code", "")
                                if code in FATAL_ERROR_CODES:
                                    raise FatalAPIError(
                                        f"Fatal ({code}): "
                                        f"{ej['error'].get('message', '')}"
                                    )
                            except (json.JSONDecodeError, FatalAPIError) as e:
                                if isinstance(e, FatalAPIError):
                                    raise

                            if retry < MAX_RETRIES - 1:
                                await asyncio.sleep(
                                    RETRY_DELAY_BASE * (retry + 1)
                                )
                            else:
                                return {
                                    "success": False,
                                    "error": f"HTTP {resp.status}",
                                }

                except asyncio.TimeoutError:
                    self.logger.warning(
                        f"[{criteria_name}] Timeout "
                        f"(retry {retry+1}/{MAX_RETRIES})"
                    )
                    if retry < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY_BASE * (retry + 1))
                    else:
                        return {"success": False, "error": "Timeout"}

                except FatalAPIError:
                    raise

                except Exception as e:
                    self.logger.error(
                        f"[{criteria_name}] Error "
                        f"(retry {retry+1}/{MAX_RETRIES}): {e}"
                    )
                    if retry < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY_BASE * (retry + 1))
                    else:
                        return {"success": False, "error": str(e)}

            return {"success": False, "error": "Max retries exceeded"}


# =============================================================================
# Response Parser
# =============================================================================

def parse_criteria_response(
    response_content: str,
    sub_criteria_list: List[str],
    criteria_name: str,
) -> Dict[str, str]:
    """Parse LLM judge response and extract per-subtype error JSON arrays."""
    try:
        # Try direct JSON parse
        text = response_content.strip()
        if text.startswith("{"):
            try:
                parsed = json.loads(text)
                return _extract_subcriteria(parsed, sub_criteria_list)
            except json.JSONDecodeError:
                pass

        # Try extracting JSON from markdown code blocks
        match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", response_content, re.DOTALL
        )
        if match:
            try:
                parsed = json.loads(match.group(1))
                return _extract_subcriteria(parsed, sub_criteria_list)
            except json.JSONDecodeError:
                pass

        # Fallback: regex extraction per sub-criteria
        results = {}
        lower = response_content.lower()
        for sc in sub_criteria_list:
            variations = [sc, sc.replace("_", " "), sc.replace("_", "-")]
            found = False
            for var in variations:
                pattern = rf"{re.escape(var.lower())}[:\s]*(\[.*?\])"
                m = re.search(pattern, lower, re.DOTALL)
                if m:
                    try:
                        json.loads(m.group(1))
                        results[sc] = m.group(1)
                        found = True
                        break
                    except json.JSONDecodeError:
                        continue
            if not found:
                results[sc] = "[]"
        return results

    except Exception:
        return {sc: "[]" for sc in sub_criteria_list}


def _extract_subcriteria(
    parsed: dict, sub_criteria_list: List[str]
) -> Dict[str, str]:
    """Extract sub-criteria values from a parsed JSON dict."""
    results = {}
    for sc in sub_criteria_list:
        if sc in parsed:
            val = parsed[sc]
            if isinstance(val, (list, dict)):
                results[sc] = json.dumps(val, ensure_ascii=False)
            else:
                results[sc] = "[]"
        else:
            results[sc] = "[]"
    return results


# =============================================================================
# ConStory-Checker Evaluator
# =============================================================================

class ConStoryChecker:
    """Main evaluation pipeline: judge each story across all 5 criteria."""

    def __init__(
        self,
        client: JudgeLLMClient,
        prompt_templates: Dict[str, str],
        story_column: str,
        logger: logging.Logger,
    ):
        self.client = client
        self.templates = prompt_templates
        self.story_column = story_column
        self.logger = logger

    async def evaluate_single(
        self,
        session: aiohttp.ClientSession,
        story_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate one story across all 5 criteria concurrently."""
        sid = story_data.get("id", story_data.get("original_id", "unknown"))
        story_text = story_data.get(self.story_column, "")

        self.logger.info(f"Evaluating story id={sid}")

        result = dict(story_data)
        result["evaluation_timestamp"] = datetime.now().isoformat()
        result["evaluation_status"] = "in_progress"
        result["judge_model"] = self.client.model

        # Initialize all columns with empty arrays
        for cat, cfg in EVALUATION_CRITERIA.items():
            for sc in cfg["sub_criteria"]:
                result[f"{cat}_{sc}"] = "[]"

        try:
            # Evaluate all 5 categories concurrently
            tasks = []
            for cat in EVALUATION_CRITERIA:
                t = self.client.evaluate_criteria(
                    session, self.templates[cat], story_text, cat
                )
                tasks.append((cat, t))

            ok = 0
            for cat, task in tasks:
                try:
                    resp = await task
                except Exception as e:
                    self.logger.error(f"[{cat}] task error: {e}")
                    resp = {"success": False, "error": str(e)}

                cfg = EVALUATION_CRITERIA[cat]
                if resp["success"]:
                    ok += 1
                    parsed = parse_criteria_response(
                        resp["content"], cfg["sub_criteria"], cat
                    )
                    for sc in cfg["sub_criteria"]:
                        result[f"{cat}_{sc}"] = parsed.get(sc, "[]")
                else:
                    err = resp.get("error", "Unknown")
                    for sc in cfg["sub_criteria"]:
                        result[f"{cat}_{sc}"] = f"ERROR: {err}"

            result["evaluation_status"] = (
                "completed" if ok == 5 else f"partial_{ok}_5"
            )
            self.logger.info(f"  id={sid}: {ok}/5 criteria completed")

        except Exception as e:
            self.logger.error(f"Critical error for id={sid}: {e}")
            result["evaluation_status"] = f"error: {e}"

        return result

    async def run(
        self,
        input_path: str,
        output_path: str,
        model_name: str,
        start_idx: int = 0,
        end_idx: Optional[int] = None,
        resume: bool = True,
    ) -> str:
        """Run the full evaluation pipeline."""
        # Load stories
        df = pd.read_parquet(input_path)
        self.logger.info(f"Loaded {len(df)} stories from {input_path}")

        if self.story_column not in df.columns:
            raise ValueError(
                f"Column '{self.story_column}' not found. "
                f"Available: {list(df.columns)}"
            )

        if end_idx is None:
            end_idx = len(df)
        df_slice = df.iloc[start_idx:end_idx]

        # Resume support
        results = []
        processed_ids = set()
        if resume and os.path.exists(output_path):
            try:
                existing = pd.read_csv(output_path)
                if "evaluation_status" in existing.columns:
                    completed = existing[
                        existing["evaluation_status"] == "completed"
                    ]
                    results = completed.to_dict("records")
                    id_col = "id" if "id" in completed.columns else "original_id"
                    processed_ids = set(completed[id_col].astype(str))
                else:
                    results = existing.to_dict("records")
                self.logger.info(f"Resuming: {len(results)} completed")
            except Exception as e:
                self.logger.warning(f"Could not load resume file: {e}")

        # Filter remaining
        to_eval = []
        id_col = "id" if "id" in df_slice.columns else "original_id"
        for _, row in df_slice.iterrows():
            if str(row.get(id_col, "")) not in processed_ids:
                to_eval.append(row.to_dict())

        self.logger.info(f"Evaluating {len(to_eval)} stories")

        # Async evaluation
        connector = aiohttp.TCPConnector(limit=50)
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT + 60)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            sem = asyncio.Semaphore(self.client.semaphore._value)

            async def _with_sem(data):
                async with sem:
                    return await self.evaluate_single(session, data)

            pbar = tqdm(
                total=len(to_eval),
                desc=f"Judging ({model_name})",
                unit="story",
            )

            batch_size = self.client.semaphore._value * 2
            for i in range(0, len(to_eval), batch_size):
                batch = to_eval[i : i + batch_size]
                batch_tasks = [_with_sem(s) for s in batch]
                batch_results = await asyncio.gather(
                    *batch_tasks, return_exceptions=True
                )

                for res in batch_results:
                    if isinstance(res, FatalAPIError):
                        self._save(results, output_path)
                        raise res
                    if isinstance(res, Exception):
                        self.logger.error(f"Batch error: {res}")
                        continue
                    results.append(res)
                    pbar.update(1)

                self._save(results, output_path)
                await asyncio.sleep(BATCH_DELAY_SECONDS)

            pbar.close()

        self._save(results, output_path)
        self.logger.info(
            f"Evaluation complete: {len(results)} stories -> {output_path}"
        )
        return output_path

    def _save(self, results: List[Dict], output_path: str):
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        pd.DataFrame(results).to_csv(
            output_path, index=False, encoding="utf-8-sig"
        )


# =============================================================================
# CLI
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="ConStory-Checker: Evaluate story consistency using LLM judge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Judge with OpenAI o4-mini (default)
  python -m constory.judge \\
      --input data/stories/my_model.parquet \\
      --story-column generated_story \\
      --model-name my_model \\
      --concurrent 3

  # Judge with a different model or self-hosted endpoint
  python -m constory.judge \\
      --input data/stories/llama3.parquet \\
      --story-column generated_story \\
      --model-name llama3 \\
      --judge-model qwen3-235b \\
      --api-base http://localhost:8000/v1 \\
      --api-key token-abc123
        """,
    )
    parser.add_argument("--input", required=True, help="Input stories parquet")
    parser.add_argument(
        "--output-dir", default="output", help="Output directory for CSV results"
    )
    parser.add_argument("--story-column", required=True, help="Story text column name")
    parser.add_argument("--model-name", required=True, help="Name for output files")
    parser.add_argument(
        "--judge-model", default="o4-mini", help="Judge model name (default: o4-mini)"
    )
    parser.add_argument(
        "--api-base",
        default="https://api.openai.com/v1",
        help="OpenAI-compatible API base URL",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENAI_API_KEY", ""),
        help="API key (default: $OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--prompts-dir",
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts"),
        help="Directory containing prompt templates",
    )
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--concurrent", type=int, default=DEFAULT_CONCURRENT)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.api_key:
        raise ValueError(
            "API key required. Set --api-key or $OPENAI_API_KEY env variable."
        )

    os.makedirs("logs", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = setup_logger("judge", f"logs/judge_{ts}.log", args.log_level)

    # Load prompt templates
    templates = load_prompt_templates(args.prompts_dir)
    logger.info(f"Loaded {len(templates)} prompt templates from {args.prompts_dir}")

    output_file = os.path.join(
        args.output_dir,
        f"judge_{args.model_name}_{args.start}_{args.end or 'end'}_{ts}.csv",
    )

    print("=" * 70)
    print("ConStory-Checker: Consistency Evaluation Pipeline")
    print("=" * 70)
    print(f"  Judge model:   {args.judge_model}")
    print(f"  API base:      {args.api_base}")
    print(f"  Input:         {args.input}")
    print(f"  Story column:  {args.story_column}")
    print(f"  Model name:    {args.model_name}")
    print(f"  Output:        {output_file}")
    print(f"  Range:         {args.start} to {args.end or 'end'}")
    print(f"  Concurrent:    {args.concurrent}")
    print(f"  Resume:        {'off' if args.no_resume else 'on'}")
    print("=" * 70)

    client = JudgeLLMClient(
        api_base=args.api_base,
        api_key=args.api_key,
        model=args.judge_model,
        max_concurrent=args.concurrent,
        logger=logger,
    )

    checker = ConStoryChecker(
        client=client,
        prompt_templates=templates,
        story_column=args.story_column,
        logger=logger,
    )

    asyncio.run(
        checker.run(
            input_path=args.input,
            output_path=output_file,
            model_name=args.model_name,
            start_idx=args.start,
            end_idx=args.end,
            resume=not args.no_resume,
        )
    )

    print(f"Done! Results saved to {output_file}")


if __name__ == "__main__":
    main()
