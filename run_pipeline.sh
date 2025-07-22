#!/bin/bash
# OKCompressor Modular Pipeline Launcher [DRAFT]
# TODO: Validate exact inputs/outputs per module and paths before running on large data.

set -e

### 0. Clone all modules if missing
# Some repos are private for now. PoC, omit them steps or test individually.
declare -A repos=(
  ["dumb_pre"]="https://github.com/OKCompressor/dumb_pre"
  ["redumb"]="https://github.com/OKCompressor/redumb"
  ["ngram-pos"]="https://github.com/GreenIshHat/ngram-pos"
  ["cc_nlp"]="https://github.com/GreenIshHat/cc_nlp"
  ["ngram-dawg"]="https://github.com/GreenIshHat/ngram-dawg"
  ["core"]="https://github.com/OKCompressor/core"
)
for dir in "${!repos[@]}"; do
  if [ ! -d "$dir" ]; then
    echo "Cloning $dir..."
    git clone "${repos[$dir]}" "$dir"
  fi
done

### 1. Paths and Parameters
INPUT_DIR="./input_dicts"         # TODO: Set your input dict location
PROC_DIR="./output_proc"
REPLACED_DIR="./output_replaced"
DAWG_OUT="./dawg_out"
BENCH_LOG="./benchmarks.tsv"

# Core pipeline scripts (fill/replace as needed)
BWT_PROC="python cc_nlp/proc_post.py"
AGG_PROC="python ngram-pos/aggregate.py"
REPLACE_PROC="python cc_nlp/replace_ngrams.py"
DAWG_PROC="python ngram-dawg/runner.py"
NGRAM_ANALYZER="python cc_nlp/ngram_analyzer.py"
COMPRESS="7z"
BENCH_LOGGER="python core/bench_logger.py"

### 2. Pipeline Stages

echo "=== [0] (Optional) dumb_pre: Preprocess Input Dicts ==="
# python dumb_pre/dumb_pre.py --input raw.txt --dict out.dict --out out.txt
# (Uncomment & fill above if you want to preprocess from raw text)

echo "=== [1] BWT+MTF transform (CC-NLP) ==="
$BWT_PROC --input "$INPUT_DIR" --output "$PROC_DIR"

echo "=== [2] Aggregate n-grams (ngram-pos) ==="
$AGG_PROC --indir "$PROC_DIR" --mode nsweep --n_max 9 --n_min 4 --min_freq 3 --output "./ngrams_dicts.npz"
# TODO: Confirm if .tsv also exported or add conversion

echo "=== [3] N-gram Analyzer (Semantic/Similarity Grouping) ==="
$NGRAM_ANALYZER --freqs "./ngrams_dicts.tsv" --out "./codebook.json" --split-mode elbow --edit-cluster

echo "=== [4] Replace n-grams with codebook ==="
$REPLACE_PROC --ngram_db "./ngrams_temp.db" --input_dir "$PROC_DIR" --output_dir "$REPLACED_DIR"

echo "=== [5] (Optional) DAWG Build ==="
$DAWG_PROC --input "$REPLACED_DIR" --outdir "$DAWG_OUT"
# Note: Restoration not yet working, for lookup speed only

echo "=== [6] Compress for benchmarking (7z) ==="
$COMPRESS a output_proc_bwtmtf_dicts.7z "$PROC_DIR"/*.bwtmtf.txt

# (Optional: Try fcmix/cmix/crux transform here—see TODO)

echo "=== [7] Log Benchmark Results ==="
$BENCH_LOGGER --indir "$REPLACED_DIR" --out "$BENCH_LOG"

echo "Pipeline finished successfully."
