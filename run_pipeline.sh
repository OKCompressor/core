#!/bin/bash
# OKCompressor Modular Pipeline Launcher [v0.2]
# All modules cloned inside modules/ (auto .gitignore)
set -e

### 0. Clone all modules inside modules/
MOD_DIR="modules"
mkdir -p "$MOD_DIR"

declare -A repos=(
  ["dumb_pre"]="git@github.com:OKCompressor/dumb_pre.git"
  ["redumb"]="git@github.com:OKCompressor/redumb.git"
  ["ngram-pos"]="git@github.com:GreenIshHat/ngram-pos.git"
  ["cc_nlp"]="git@github.com:GreenIshHat/cc_nlp.git"
  ["ngram-dawg"]="git@github.com:GreenIshHat/ngram-dawg.git"
  ["core"]="git@github.com:OKCompressor/core.git"
)

for dir in "${!repos[@]}"; do
  if [ ! -d "$MOD_DIR/$dir" ]; then
    echo "Cloning $dir..."
    git clone "${repos[$dir]}" "$MOD_DIR/$dir"
  fi
done

# Ensure .gitignore contains modules/
if ! grep -q "^modules/$" .gitignore 2>/dev/null; then
  echo "modules/" >> .gitignore
  echo "Added 'modules/' to .gitignore"
fi

### 1. Paths and Parameters
INPUT_DIR="./input_dicts"         # TODO: Set your input dict location
PROC_DIR="./output_proc"
REPLACED_DIR="./output_replaced"
DAWG_OUT="./dawg_out"
BENCH_LOG="./benchmarks.tsv"

# Core pipeline scripts (all module paths now prefixed with $MOD_DIR/)
BWT_PROC="python $MOD_DIR/cc_nlp/proc_post.py"
AGG_PROC="python $MOD_DIR/ngram-pos/aggregate.py"
REPLACE_PROC="python $MOD_DIR/cc_nlp/replace_ngrams.py"
DAWG_PROC="python $MOD_DIR/ngram-dawg/runner.py"
NGRAM_ANALYZER="python $MOD_DIR/cc_nlp/ngram_analyzer.py"
COMPRESS="7z"
BENCH_LOGGER="python $MOD_DIR/core/bench_logger.py"

### 2. Pipeline Stages

echo "=== [0] (Optional) dumb_pre: Preprocess Input Dicts ==="
# Example (uncomment to use):
# python $MOD_DIR/dumb_pre/dumb_pre.py --input raw.txt --dict out.dict --out out.txt

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
# Note: DAWG restoration not yet working; for lookup speed only.

echo "=== [6] Compress for benchmarking (7z) ==="
$COMPRESS a output_proc_bwtmtf_dicts.7z "$PROC_DIR"/*.bwtmtf.txt

# (Optional: Try fcmix/cmix/crux transform here—see TODO)

echo "=== [7] Log Benchmark Results ==="
$BENCH_LOGGER --indir "$REPLACED_DIR" --out "$BENCH_LOG"

echo "Pipeline finished successfully."
