#!/bin/bash
# OKCompressor Modular Pipeline Launcher (Luna-vetted, toggleable, tidy, minimal-archive)
set -ex

########## PIPELINE TOGGLES ##########
DO_BWT=1
DO_MTF=1
DO_RLE=1
CLEANUP_TMP=1
######################################

MOD_DIR="modules"
INPUT_FOLDER="data"
mkdir -p "$MOD_DIR" "$INPUT_FOLDER"

# Ensure .gitignore hygiene
for entry in modules/ output/ data/; do
  if ! grep -qx "$entry" .gitignore 2>/dev/null; then
    echo "$entry" >> .gitignore
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
    git clone "${repos[$dir]}" "$MOD_DIR/$dir"
  fi
done

INPUT_FILES=("enwik6")  # Edit as needed

for INFILE in "${INPUT_FILES[@]}"; do
  INPATH="$INPUT_FOLDER/$INFILE"
  if [ ! -f "$INPATH" ] && [ -f "$INPATH.txt" ]; then
    INPATH="$INPATH.txt"
  fi
  if [ ! -f "$INPATH" ]; then
    echo "[ERROR] Input file '$INPATH' (or .txt) not found in $INPUT_FOLDER/"
    exit 1
  fi

  BASENAME=$(basename "$INFILE" .txt)
  OUTBASE="output/$BASENAME"

  RAW_DIR="$OUTBASE/00_dumb"
  NGRAMS_DIR="$OUTBASE/03_ngrams"
  CCNLP_OUT="$OUTBASE/ccnlp"
  BWT_DIR="$OUTBASE/01_bwt"
  MTF_DIR="$OUTBASE/02_mtf"
  REPLACED_DIR="$OUTBASE/04_replaced"
  FINAL_DIR="$OUTBASE/99_final"
  DAWG_DIR="$OUTBASE/05_dawg"
  BENCH_LOG="$OUTBASE/benchmarks.tsv"
  ARCHIVE="$OUTBASE/compressed.7z"
  DB="$NGRAMS_DIR/ngrams_temp.db"
  CODEBOOK_TXT="$NGRAMS_DIR/ngram_used_codebook.txt"
  CODEBOOK_NPZ="$NGRAMS_DIR/ngram_used_codebook.npz"

  mkdir -p "$RAW_DIR" "$CCNLP_OUT" "$NGRAMS_DIR" "$REPLACED_DIR" "$FINAL_DIR" "$DAWG_DIR"

  #### [0] Dumb Preprocessing ####
  echo "=== [$BASENAME] [0] Preprocess (dumb_pre) ==="
  if [ -f "$MOD_DIR/dumb_pre/dumb_pre_v2.py" ]; then
    python "$MOD_DIR/dumb_pre/dumb_pre_v2.py" \
      --input "$INPATH" \
      --dict "$RAW_DIR/dict.txt" \
      --out "$RAW_DIR/output.txt"
    PREV_OUT="$RAW_DIR/output.txt"
  else
    echo "[Luna] dumb_pre_v2.py not found, using input as-is."
    PREV_OUT="$INPATH"
  fi

  #### [1] CC-NLP Category Chunking ####
  echo "=== [$BASENAME] [1] CC-NLP Category Chunking ==="
  if [ -f "$MOD_DIR/cc_nlp/chunked_encode.py" ]; then
    python "$MOD_DIR/cc_nlp/chunked_encode.py" \
      --dumb_path "$RAW_DIR" \
      --dict_file "dict.txt" \
      --pos_file "output.txt" \
      --outdir "$CCNLP_OUT" \
      --chunk_size 1000000
  else
    echo "[Luna] chunked_encode.py not found, skipping CC-NLP chunking."
  fi

  #### [2] N-gram Aggregation (CC-NLP subidx) ####
  echo "=== [$BASENAME] [2] Aggregate n-grams (ngram-pos, CC-NLP) ==="
  python $MOD_DIR/ngram-pos/aggregate.py \
    --indir "$CCNLP_OUT" \
    --pattern "sub_idxs_*.npy" \
    --n_max 13 \
    --n_min 3 \
    --output "$NGRAMS_DIR/ngrams_dicts.npz" \
    --sqlite_db "$NGRAMS_DIR/ngrams_temp.db"



  #### [3] N-gram Replacement (CC-NLP) ####
  echo "=== [$BASENAME] [3] Replace n-grams with codebook ==="
  if [ -f "$MOD_DIR/ngram-pos/replace_ngrams.py" ]; then
    python $MOD_DIR/ngram-pos/replace_ngrams.py \
      --input_dir "$CCNLP_OUT" \
      --output_dir "$REPLACED_DIR" \
      --ngram_db "$DB" \
      --final_codebook_txt "$CODEBOOK_TXT" \
      --final_codebook_npz "$CODEBOOK_NPZ" \
      --min_freq 7 \
      --start_code 1000000 \
      --pattern "sub_idxs_*.npy"
  else
    echo "[Luna] replace_ngrams.py not found, skipping n-gram replacement."
  fi


# add aggregator + replace step for only 2 n-grams check worth as weight len x freq vs dict entrie len

  #### [4] BWT/MTF/RLE (post-ngram, each replaced chunk) ####
for f in $REPLACED_DIR/repl_subidx_*.npy; do
  [ -e "$f" ] || continue  # skip if no match
  fn=$(basename "$f" .npy)
  TMP_BWT="$FINAL_DIR/${fn}.bwt.txt"
  TMP_MTF="$FINAL_DIR/${fn}.bwtmtf.txt"
  OUT_RLE="$FINAL_DIR/${fn}_bwtmtfrle.txt"

  if (( DO_BWT )); then
    python $MOD_DIR/crux2/crux2_bwt.py --input "$f" --output "$TMP_BWT"
  fi
  if (( DO_MTF )); then
    python $MOD_DIR/crux2/crux2_mtf.py --input "$TMP_BWT" --output "$TMP_MTF" --alphabet_mode global
  fi
  if (( DO_RLE )); then
    python $MOD_DIR/crux2/crux2_rle.py --input "$TMP_MTF" --output "$OUT_RLE"
  fi
  if (( CLEANUP_TMP )); then
    rm -f "$TMP_BWT" "$TMP_MTF"
  fi
done


echo "=== [$BASENAME] [7] Dicts: BWT→MTF→RLE ==="
DICT_FINAL_DIR="$OUTBASE/99_dicts_final"
mkdir -p "$DICT_FINAL_DIR"

# For every commons/uniqs dict in the CCNLP output
for f in "$CCNLP_OUT"/cat*_*.txt; do
  [ -f "$f" ] || continue
  flat="$DICT_FINAL_DIR/$(basename "${f%.txt}").flat.txt"
  bwt="$DICT_FINAL_DIR/$(basename "${f%.txt}").bwt.txt"
  mtf="$DICT_FINAL_DIR/$(basename "${f%.txt}").bwtmtf.txt"
  rle="$DICT_FINAL_DIR/$(basename "${f%.txt}")_bwtmtfrle.txt"

  # 1. Flatten to a single line (space-separated)
  paste -sd ' ' "$f" > "$flat"

  # 2. BWT
  python $MOD_DIR/crux2/crux2_bwt.py --input "$flat" --output "$bwt"

  # 3. MTF
  python $MOD_DIR/crux2/crux2_mtf.py --input "$bwt" --output "$mtf"

  # 4. RLE
  python $MOD_DIR/crux2/crux2_rle.py --input "$mtf" --output "$rle"
done


  #### [5] Minimal Archive (final output) ####
  echo "=== [$BASENAME] [5] Compress for benchmarking (7z, minimal set) ==="
  7z a -mx=9 "$ARCHIVE" \
    "$FINAL_DIR"/*_bwtmtfrle.txt \
    "$CCNLP_OUT"/cats_*.base4 \

    # "$CCNLP_OUT"/cat*_commons.txt \
    # "$CCNLP_OUT"/cat*_uniqs.txt \
    "$DICT_FINAL_DIR"/*_bwtmtfrle.txt \

    "$CODEBOOK_TXT"

  #### [6] (Optional) Log Benchmark Results ####
  echo "=== [$BASENAME] [6] Log Benchmark Results ==="
  if [ -f "$MOD_DIR/core/bench_logger.py" ]; then
    python $MOD_DIR/core/bench_logger.py --indir "$FINAL_DIR" --out "$BENCH_LOG"
  else
    echo "[Luna] bench_logger.py not found, skipping benchmark log."
  fi

  echo "=== [$BASENAME] Pipeline finished successfully ==="
done
