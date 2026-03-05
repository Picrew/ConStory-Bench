#!/bin/bash
# ConStory-Bench: Story Generation Examples
# Uses OpenAI-compatible API for all models

set -e
export PYTHONUNBUFFERED=1

# ==================== Configuration ====================
# Set your API credentials (or export them before running)
API_KEY="${OPENAI_API_KEY:?Please set OPENAI_API_KEY}"
API_BASE="${API_BASE:-https://api.openai.com/v1}"
INPUT="data/prompts.parquet"
OUTPUT_DIR="data/stories"
CONCURRENT=5

mkdir -p "$OUTPUT_DIR"

# ==================== Generate Stories ====================
# Example: GPT-4o
echo ">>> Generating stories with GPT-4o..."
python -m constory.generate \
    --input "$INPUT" \
    --output "$OUTPUT_DIR/gpt4o.parquet" \
    --model "gpt-4o" \
    --api-base "$API_BASE" \
    --api-key "$API_KEY" \
    --max-tokens 16384 \
    --concurrent "$CONCURRENT" \
    --story-column "generated_story"

# Example: Using a local vLLM server
# echo ">>> Generating stories with Llama-3..."
# python -m constory.generate \
#     --input "$INPUT" \
#     --output "$OUTPUT_DIR/llama3.parquet" \
#     --model "meta-llama/Llama-3-70B-Instruct" \
#     --api-base "http://localhost:8000/v1" \
#     --api-key "token-abc123" \
#     --max-tokens 16384 \
#     --concurrent 3 \
#     --story-column "generated_story"

echo "Done! Stories saved to $OUTPUT_DIR/"
