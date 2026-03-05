#!/bin/bash
# ConStory-Bench: Consistency Evaluation (ConStory-Checker) Examples
# Uses OpenAI-compatible API for the judge model

set -e
export PYTHONUNBUFFERED=1

# ==================== Configuration ====================
API_KEY="${OPENAI_API_KEY:?Please set OPENAI_API_KEY}"
API_BASE="${API_BASE:-https://api.openai.com/v1}"
JUDGE_MODEL="${JUDGE_MODEL:-o4-mini}"
STORIES_DIR="data/stories"
OUTPUT_DIR="output"
CONCURRENT=3

mkdir -p "$OUTPUT_DIR"

# ==================== Helper Function ====================
run_judge() {
    local MODEL_NAME=$1
    local STORY_FILE=$2
    local STORY_COL=${3:-generated_story}

    echo ">>> Evaluating ${MODEL_NAME} with judge ${JUDGE_MODEL}..."
    python -m constory.judge \
        --input "$STORIES_DIR/$STORY_FILE" \
        --story-column "$STORY_COL" \
        --model-name "$MODEL_NAME" \
        --judge-model "$JUDGE_MODEL" \
        --api-base "$API_BASE" \
        --api-key "$API_KEY" \
        --output-dir "$OUTPUT_DIR" \
        --concurrent "$CONCURRENT"
    echo ">>> ${MODEL_NAME} done."
    echo ""
}

# ==================== Run Evaluations ====================
# Example: Evaluate GPT-4o stories
run_judge "gpt4o" "gpt4o.parquet"

# Example: Evaluate with a self-hosted judge
# JUDGE_MODEL="qwen3-235b" API_BASE="http://localhost:8000/v1" \
#     run_judge "llama3" "llama3.parquet"

echo "All evaluations complete! Results saved to $OUTPUT_DIR/"
