#!/bin/bash
# OKCompressor Modular Pipeline Launcher (fully parametric, per-file)
set -ex

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
  
  DB="$NGRAMS_DIR/ngrams_temp.db"
  CODEBOOK_TXT="$NGRAMS_DIR/ngram_used_codebook.txt"
  CODEBOOK_NPZ="$NGRAMS_DIR/ngram_used_codebook.npz"

  REPLACED_DIR="$OUTBASE/04_replaced"
  DAWG_DIR="$OUTBASE/05_dawg"
  BENCH_LOG="$OUTBASE/benchmarks.tsv"
  ARCHIVE="$OUTBASE/compressed.7z"



  mkdir -p "$RAW_DIR" "$BWT_DIR" "$MTF_DIR" "$NGRAMS_DIR" "$REPLACED_DIR" "$DAWG_DIR"

  echo "=== [$BASENAME] [0] Optional: Preprocess Raw Input (dumb_pre) ==="
  if [ -f "$MOD_DIR/dumb_pre/dumb_pre_v2.py" ]; then
    time python $MOD_DIR/dumb_pre/dumb_pre_v2.py \
        --input "$INPATH" \
        --dict "$RAW_DIR/dict.txt" \
        --out "$RAW_DIR/output.txt"
    PREV_OUT="$RAW_DIR/output.txt"


  else
    echo "dumb_pre_v2.py not found, skipping. Using input file as is."
    PREV_OUT="$INPATH"
  fi
  
  
  ## ccnlp cats needs to proc files here
  # then it gens subidxs and dict per cat: commons and uniqs
  # chunked_encode.py
  # CC-NLP Compression Pipeline
# /*
# A simple, frequency-aware token compressor built on top of a “dumb” tokenization of enwik8:

# - **Input**:  
#   - `enwik8` raw text  
#   - Precomputed token IDs + dictionary (via `okc.dumb` or Rust-port `redumb` / `dumb_pre`)  
# - **Output** (`output/`):  
#   - **Per-category globals**:  
#     - `cat0_commons.txt` & `cat0_uniqs.txt`  
#     - `cat1_commons.txt` & `cat1_uniqs.txt`  
#     - `cat2_commons.txt` & `cat2_uniqs.txt`  
#     - `cat3_commons.txt` & `cat3_uniqs.txt`  
#   - **Chunked streams** (1 M tokens each):  
#     - `cats_{offset}.base4` + `.n` (packed 2-bit/category)  
#     - `sub_idxs_{offset}.npy` (uint32 sub-index per token)  

# When compressed (7z), the entire `output/` folder clocks in at **≈ 29.6 MB** for the full 100 M-byte enwik8 dataset.

# ---
# */
# # adjusst accordingly so on, mb time  to do the py script version


  

# will need to plug rust crux1 versioooon port WIP
  echo "=== [$BASENAME] [1] BWT transform (crux2) ==="
  #python $MOD_DIR/crux2/crux2_bwt.py --input "$PREV_OUT" --output "$BWT_DIR"
  time python $MOD_DIR/crux2/crux2_bwt.py --input "$PREV_OUT" --output "$BWT_DIR" --chunk-mode bytes --chunk-size 32000

  echo "=== [$BASENAME] [2] MTF transform (crux2) ==="
  python $MOD_DIR/crux2/crux2_mtf.py --input "$BWT_DIR" --output "$MTF_DIR" --alphabet_mode global

echo "+++ crux2::rle +++"
python $MOD_DIR/crux2/crux2_rle.py \
    --input "$MTF_DIR/output.mtf.txt" \
    --output "$MTF_DIR/output.mtf.rle.txt"

  echo "=== [$BASENAME] [3] Aggregate n-grams (ngram-pos) ==="
  #python $MOD_DIR/ngram-pos/aggregate.py --indir "$MTF_DIR" --mode nsweep --n_max 9 --n_min 4 --min_freq 3 --output "$NGRAMS_DIR/ngrams_dicts.npz" --sqlite_db "$NGRAMS_DIR/ngrams_temp.db"
  time python $MOD_DIR/ngram-pos/aggregate.py --indir ./output/enwik7/02_mtf --pattern "*.mtf.rle.txt" --n_max 13 --n_min 3 --output ./output/enwik7/03_ngrams/ngrams_dicts.npz --sqlite_db ./output/enwik7/03_ngrams/ngrams_temp.db


  # echo "=== [$BASENAME] [4] N-gram Analyzer (Semantic/Similarity Grouping) ==="
  # if [ -f "$MOD_DIR/cc_nlp/ngram_analyzer.py" ]; then
  #   python $MOD_DIR/cc_nlp/ngram_analyzer.py --freqs "$NGRAMS_DIR/ngrams_dicts.tsv" --out "$NGRAMS_DIR/codebook.json" --split-mode elbow --edit-cluster
  # else
  #   echo "ngram_analyzer.py not found, skipping this stage."
  # fi

  echo "=== [$BASENAME] [5] Replace n-grams with codebook ==="
  if [ -f "$MOD_DIR/ngram-pos/replace_ngrams.py" ]; then
    # python $MOD_DIR/ngram-pos/replace_ngrams.py --ngram_db "$NGRAMS_DIR/ngrams_temp.db" --input_dir "$MTF_DIR" --output_dir "$REPLACED_DIR"
    # N-gram replacement (now flexible)
    python $MOD_DIR/ngram-pos/replace_ngrams.py \
    --input_dir "$MTF_DIR" \
    --output_dir "$REPLACED_DIR" \
    --ngram_db "$DB" \
    --final_codebook_txt "$CODEBOOK_TXT" \
    --final_codebook_npz "$CODEBOOK_NPZ" \
    --min_freq 7 \
    --start_code 1_000_000 \
    --pattern "*.mtf.txt"   # or "sub_idxs_*.npy" as needed
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
