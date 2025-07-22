#!/bin/bash
# OKCompressor Modular Pipeline Launcher (fully parametric, per-file)
set -e

MOD_DIR="modules"
INPUT_FOLDER="data"
mkdir -p "$MOD_DIR" "$INPUT_FOLDER"

# Add .gitignore entries if missing
for entry in modules/ output/ data/; do
  if ! grep -qx "$entry" .gitignore 2>/dev/null; then
    echo "$entry" >> .gitignore
    echo "Added '$entry' to .gitignore"
  fi
done

declare -A repos=(
  ["dumb_pre"]="git@github.com:OKCompressor/dumb_pre.git"
  ["redumb"]="git@github.com:OKCompressor/redumb.git"
  ["ngram-pos"]="git@github.com:GreenIshHat/ngram-pos.git"
  ["cc_nlp"]="git@github.com:GreenIshHat/cc_nlp.git"
  ["ngram-dawg"]="git@github.com:GreenIshHat/ngram-dawg.git"
  ["crux2"]="git@github.com:GreenIshHat/crux2.git"
  ["core"]="git@github.com:OKCompressor/core.git"
)

for dir in "${!repos[@]}"; do
  if [ ! -d "$MOD_DIR/$dir" ]; then
    echo "Cloning $dir..."
    git clone "${repos[$dir]}" "$MOD_DIR/$dir"
  fi
done

# === Inputs (list one or more, extensionless or with .txt)
INPUT_FILES=("enwik7")  # Edit as needed

for INFILE in "${INPUT_FILES[@]}"; do
  INPATH="$INPUT_FOLDER/$INFILE"
  if [ ! -f "$INPATH" ]; then
    if [ -f "$INPATH.txt" ]; then
      INPATH="$INPATH.txt"
    else
      echo "[ERROR] Input file '$INPATH' (or .txt) not found in $INPUT_FOLDER/"
      exit 1
    fi
  fi
  BASENAME=$(basename "$INFILE" .txt)
  OUTBASE="output/$BASENAME"
  mkdir -p "$OUTBASE"

  RAW_DIR="$OUTBASE/00_dumb"
  BWT_DIR="$OUTBASE/01_bwt"
  MTF_DIR="$OUTBASE/02_mtf"
  NGRAMS_DIR="$OUTBASE/03_ngrams"
  REPLACED_DIR="$OUTBASE/04_replaced"
  DAWG_DIR="$OUTBASE/05_dawg"
  BENCH_LOG="$OUTBASE/benchmarks.tsv"
  ARCHIVE="$OUTBASE/compressed.7z"

  mkdir -p "$RAW_DIR" "$BWT_DIR" "$MTF_DIR" "$NGRAMS_DIR" "$REPLACED_DIR" "$DAWG_DIR"

  echo "=== [$BASENAME] [0] Optional: Preprocess Raw Input (dumb_pre) ==="
  if [ -f "$MOD_DIR/dumb_pre/dumb_pre_v2.py" ]; then
    python $MOD_DIR/dumb_pre/dumb_pre_v2.py \
        --input "$INPATH" \
        --dict "$RAW_DIR/dict.txt" \
        --out "$RAW_DIR/output.txt"
    PREV_OUT="$RAW_DIR/output.txt"


  else
    echo "dumb_pre_v2.py not found, skipping. Using input file as is."
    PREV_OUT="$INPATH"
  fi

  echo "=== [$BASENAME] [1] BWT transform (crux2) ==="
  #python $MOD_DIR/crux2/crux2_bwt.py --input "$PREV_OUT" --output "$BWT_DIR"
  python $MOD_DIR/crux2/crux2_bwt.py --input "$PREV_OUT" --output "$BWT_DIR" --chunk-mode bytes --chunk-size 64000


  echo "=== [$BASENAME] [2] MTF transform (crux2) ==="
  python $MOD_DIR/crux2/crux2_mtf.py --input "$BWT_DIR" --output "$MTF_DIR" --alphabet_mode global

  echo "=== [$BASENAME] [3] Aggregate n-grams (ngram-pos) ==="
  python $MOD_DIR/ngram-pos/aggregate.py --indir "$MTF_DIR" --mode nsweep --n_max 9 --n_min 4 --min_freq 3 --output "$NGRAMS_DIR/ngrams_dicts.npz" --sqlite_db "$NGRAMS_DIR/ngrams_temp.db"

  echo "=== [$BASENAME] [4] N-gram Analyzer (Semantic/Similarity Grouping) ==="
  if [ -f "$MOD_DIR/cc_nlp/ngram_analyzer.py" ]; then
    python $MOD_DIR/cc_nlp/ngram_analyzer.py --freqs "$NGRAMS_DIR/ngrams_dicts.tsv" --out "$NGRAMS_DIR/codebook.json" --split-mode elbow --edit-cluster
  else
    echo "ngram_analyzer.py not found, skipping this stage."
  fi

  echo "=== [$BASENAME] [5] Replace n-grams with codebook ==="
  if [ -f "$MOD_DIR/cc_nlp/replace_ngrams.py" ]; then
    python $MOD_DIR/cc_nlp/replace_ngrams.py --ngram_db "$NGRAMS_DIR/ngrams_temp.db" --input_dir "$MTF_DIR" --output_dir "$REPLACED_DIR"
  else
    echo "replace_ngrams.py not found, skipping this stage."
  fi

  echo "=== [$BASENAME] [6] (Optional) DAWG Build ==="
  if [ -f "$MOD_DIR/ngram-dawg/runner.py" ]; then
    python modules/ngram-dawg/runner.py \
  --dicts "output/enwik7/04_replaced/*.txt" \
  --outdir "output/enwik7/05_dawg"

  else
    echo "runner.py not found in ngram-dawg, skipping DAWG build."
  fi

  echo "=== [$BASENAME] [7] Compress for benchmarking (7z) ==="
  7z a -mx=9 "$ARCHIVE" "$MTF_DIR"/*.txt

  echo "=== [$BASENAME] [8] Log Benchmark Results ==="
  if [ -f "$MOD_DIR/core/bench_logger.py" ]; then
    python $MOD_DIR/core/bench_logger.py --indir "$REPLACED_DIR" --out "$BENCH_LOG"
  else
    echo "bench_logger.py not found, skipping benchmark log."
  fi

  echo "=== [$BASENAME] Pipeline finished successfully ==="

done
