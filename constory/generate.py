#!/usr/bin/env python
# coding: utf-8
"""
Story Generation Pipeline for ConStory-Bench

Generates long-form stories from benchmark prompts using any OpenAI-compatible API.
Supports async concurrent generation with resume capability.

Usage:
    python -m constory.generate \
        --input data/prompts.parquet \
        --output data/stories/my_model.parquet \
        --model gpt-4o \
        --api-base https://api.openai.com/v1 \
        --api-key $OPENAI_API_KEY \
        --concurrent 5
"""

import os
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

DEFAULT_MAX_TOKENS = 16384
DEFAULT_TEMPERATURE = 0.7
DEFAULT_CONCURRENT = 3
MAX_RETRIES = 3
RETRY_DELAY_BASE = 5
REQUEST_TIMEOUT = 600
CONNECT_TIMEOUT = 30

FATAL_ERROR_CODES = {
    "Arrearage", "InvalidApiKey", "Unauthorized",
    "AccountDisabled", "InsufficientBalance",
}


class FatalAPIError(Exception):
    """Raised when an unrecoverable API error is detected."""
    pass


# =============================================================================
# Logging
# =============================================================================

def setup_logger(name: str, log_file: str, level: str = "INFO") -> logging.Logger:
    """Set up logger with file and console handlers."""
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
# OpenAI-Compatible LLM Client
# =============================================================================

class OpenAIClient:
    """Async client for any OpenAI-compatible API endpoint."""

    def __init__(
        self,
        api_base: str,
        api_key: str,
        model: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        max_concurrent: int = DEFAULT_CONCURRENT,
        logger: Optional[logging.Logger] = None,
    ):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = logger or logging.getLogger(__name__)

    async def generate(
        self,
        session: aiohttp.ClientSession,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a chat completion request with retry logic."""
        async with self.semaphore:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
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
                            content = result["choices"][0]["message"]["content"]
                            return {"success": True, "content": content}
                        else:
                            error_text = await resp.text()
                            self.logger.warning(
                                f"API error (retry {retry+1}/{MAX_RETRIES}): "
                                f"HTTP {resp.status}: {error_text[:200]}"
                            )
                            # Check for fatal errors
                            try:
                                ej = json.loads(error_text)
                                code = ej.get("error", {}).get("code", "")
                                if code in FATAL_ERROR_CODES:
                                    raise FatalAPIError(
                                        f"Fatal API error ({code}): "
                                        f"{ej['error'].get('message', '')}"
                                    )
                            except (json.JSONDecodeError, FatalAPIError) as e:
                                if isinstance(e, FatalAPIError):
                                    raise

                            if retry < MAX_RETRIES - 1:
                                await asyncio.sleep(RETRY_DELAY_BASE * (retry + 1))
                            else:
                                return {
                                    "success": False,
                                    "error": f"HTTP {resp.status}: {error_text[:200]}",
                                }

                except asyncio.TimeoutError:
                    self.logger.warning(
                        f"Timeout (retry {retry+1}/{MAX_RETRIES})"
                    )
                    if retry < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY_BASE * (retry + 1))
                    else:
                        return {"success": False, "error": "Timeout after retries"}

                except FatalAPIError:
                    raise

                except Exception as e:
                    self.logger.error(
                        f"Error (retry {retry+1}/{MAX_RETRIES}): {e}"
                    )
                    if retry < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY_BASE * (retry + 1))
                    else:
                        return {"success": False, "error": str(e)}

            return {"success": False, "error": "Max retries exceeded"}


# =============================================================================
# Story Generator
# =============================================================================

class StoryGenerator:
    """Generate long-form stories from ConStory-Bench prompts."""

    SYSTEM_PROMPT = (
        "You are a talented fiction writer. Given a story prompt, write a "
        "detailed, engaging, and coherent long-form narrative. Focus on "
        "rich character development, consistent world-building, and logical "
        "plot progression. Maintain consistency throughout the entire story."
    )

    def __init__(
        self,
        client: OpenAIClient,
        logger: logging.Logger,
        story_column: str = "generated_story",
    ):
        self.client = client
        self.logger = logger
        self.story_column = story_column

    async def generate_single(
        self,
        session: aiohttp.ClientSession,
        row: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate a story for a single prompt."""
        prompt_text = row.get("prompt", "")
        story_id = row.get("id", "unknown")

        self.logger.info(f"Generating story for id={story_id}")

        result = dict(row)
        result["generation_timestamp"] = datetime.now().isoformat()

        resp = await self.client.generate(
            session, prompt_text, system_prompt=self.SYSTEM_PROMPT
        )

        if resp["success"]:
            result[self.story_column] = resp["content"]
            result["generation_error"] = None
            word_count = len(resp["content"].split())
            self.logger.info(
                f"  id={story_id}: generated {word_count} words"
            )
        else:
            result[self.story_column] = None
            result["generation_error"] = resp.get("error", "Unknown error")
            self.logger.error(
                f"  id={story_id}: generation failed - {resp.get('error')}"
            )

        return result

    async def run(
        self,
        input_path: str,
        output_path: str,
        start_idx: int = 0,
        end_idx: Optional[int] = None,
        resume: bool = True,
    ) -> str:
        """Run story generation pipeline."""
        # Load prompts
        df = pd.read_parquet(input_path)
        self.logger.info(f"Loaded {len(df)} prompts from {input_path}")

        if end_idx is None:
            end_idx = len(df)
        df_slice = df.iloc[start_idx:end_idx]
        self.logger.info(f"Processing prompts {start_idx} to {end_idx - 1}")

        # Resume support
        results = []
        processed_ids = set()
        if resume and os.path.exists(output_path):
            try:
                existing = pd.read_parquet(output_path)
                valid = existing[existing[self.story_column].notna()]
                results = valid.to_dict("records")
                processed_ids = set(valid["id"].astype(str))
                self.logger.info(f"Resuming: {len(results)} already completed")
            except Exception as e:
                self.logger.warning(f"Could not load existing results: {e}")

        # Filter remaining
        to_process = []
        for _, row in df_slice.iterrows():
            if str(row.get("id", "")) not in processed_ids:
                to_process.append(row.to_dict())

        self.logger.info(f"Generating {len(to_process)} new stories")

        # Async generation
        connector = aiohttp.TCPConnector(limit=50)
        async with aiohttp.ClientSession(connector=connector) as session:
            pbar = tqdm(total=len(to_process), desc="Generating", unit="story")

            batch_size = self.client.semaphore._value * 2
            for i in range(0, len(to_process), batch_size):
                batch = to_process[i : i + batch_size]
                tasks = [self.generate_single(session, row) for row in batch]
                batch_results = await asyncio.gather(
                    *tasks, return_exceptions=True
                )

                for res in batch_results:
                    if isinstance(res, FatalAPIError):
                        self.logger.error(f"Fatal error: {res}")
                        self._save(results, output_path)
                        raise res
                    if isinstance(res, Exception):
                        self.logger.error(f"Batch error: {res}")
                        continue
                    results.append(res)
                    pbar.update(1)

                # Save incrementally
                self._save(results, output_path)

            pbar.close()

        self._save(results, output_path)
        self.logger.info(
            f"Generation complete: {len(results)} stories saved to {output_path}"
        )
        return output_path

    def _save(self, results: List[Dict], output_path: str):
        """Save results to parquet."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        pd.DataFrame(results).to_parquet(output_path, index=False)


# =============================================================================
# CLI
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="ConStory-Bench: Generate long-form stories using OpenAI-compatible APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate with OpenAI
  python -m constory.generate \\
      --input data/prompts.parquet \\
      --output data/stories/gpt4o.parquet \\
      --model gpt-4o --concurrent 5

  # Generate with a local vLLM server
  python -m constory.generate \\
      --input data/prompts.parquet \\
      --output data/stories/llama3.parquet \\
      --model meta-llama/Llama-3-70B-Instruct \\
      --api-base http://localhost:8000/v1 \\
      --api-key token-abc123
        """,
    )
    parser.add_argument("--input", required=True, help="Input prompts parquet file")
    parser.add_argument("--output", required=True, help="Output stories parquet file")
    parser.add_argument("--model", required=True, help="Model name for the API")
    parser.add_argument(
        "--api-base",
        default="https://api.openai.com/v1",
        help="OpenAI-compatible API base URL (default: OpenAI)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENAI_API_KEY", ""),
        help="API key (default: $OPENAI_API_KEY)",
    )
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--concurrent", type=int, default=DEFAULT_CONCURRENT)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument(
        "--story-column",
        default="generated_story",
        help="Column name for generated story text",
    )
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
            "API key required. Set --api-key or $OPENAI_API_KEY environment variable."
        )

    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = setup_logger(
        "generate", f"logs/generate_{timestamp}.log", args.log_level
    )

    print("=" * 70)
    print("ConStory-Bench Story Generation Pipeline")
    print("=" * 70)
    print(f"  Model:       {args.model}")
    print(f"  API base:    {args.api_base}")
    print(f"  Input:       {args.input}")
    print(f"  Output:      {args.output}")
    print(f"  Range:       {args.start} to {args.end or 'end'}")
    print(f"  Concurrent:  {args.concurrent}")
    print(f"  Max tokens:  {args.max_tokens}")
    print(f"  Resume:      {'off' if args.no_resume else 'on'}")
    print("=" * 70)

    client = OpenAIClient(
        api_base=args.api_base,
        api_key=args.api_key,
        model=args.model,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        max_concurrent=args.concurrent,
        logger=logger,
    )

    generator = StoryGenerator(
        client=client, logger=logger, story_column=args.story_column
    )

    asyncio.run(
        generator.run(
            input_path=args.input,
            output_path=args.output,
            start_idx=args.start,
            end_idx=args.end,
            resume=not args.no_resume,
        )
    )

    print("Done!")


if __name__ == "__main__":
    main()
