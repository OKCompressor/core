#!/bin/bash
# OKCompressor Modular Pipeline Launcher (Luna-vetted, toggleable, tidy, minimal-archive)
set -e

########## PIPELINE TOGGLES ##########
DO_BWT=1
DO_MTF=1
DO_RLE=1
CLEANUP_TMP=1
######################################

MOD_DIR="modules"
INPUT_FOLDER="data"
mkdir -p "$MOD_DIR" "$INPUT_FOLDER"

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

INPUT_FILES=("enwik5")  # Edit as needed

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

#   #### [3b] EXTRA: Aggregate & Replace 2-grams only (low-mem) ####
# echo "=== [$BASENAME] [3b] Aggregate 2-grams only (ngram-pos, CC-NLP) ==="
# python $MOD_DIR/ngram-pos/aggregate.py \
#   --indir "$REPLACED_DIR" \
#   --pattern "repl_sub_idxs_*.npy" \
#   --n_max 2 \
#   --n_min 2 \
#   --output "$NGRAMS_DIR/ngrams_2gram_only.npz" \
#   --sqlite_db "$NGRAMS_DIR/ngrams_2gram_only.db"

# echo "=== [$BASENAME] [3c] Replace 2-grams only ==="
# python $MOD_DIR/ngram-pos/replace_ngrams.py \
#   --input_dir "$REPLACED_DIR" \
#   --output_dir "$REPLACED_DIR" \
#   --ngram_db "$NGRAMS_DIR/ngrams_2gram_only.db" \
#   --final_codebook_txt "$NGRAMS_DIR/ngram_2gram_codebook.txt" \
#   --final_codebook_npz "$NGRAMS_DIR/ngram_2gram_codebook.npz" \
#   --min_freq 7 \
#   --start_code 2000000 \
#   --pattern "repl_sub_idxs_*.npy"


count=$(ls "$REPLACED_DIR"/repl_sub_idxs_*.txt 2>/dev/null | wc -l)
if (( count == 0 )); then
  echo "[Luna] ERROR: No replaced subidx files found. Check file naming and upstream steps."
  exit 2
fi

  #### [4] BWT/MTF/RLE (post-ngram, each replaced chunk) ####
#### [4] BWT/MTF/RLE (post-ngram, each replaced chunk) ####
for f in "$REPLACED_DIR"/repl_sub_idxs_*.txt; do
  [ -e "$f" ] || continue
  bn=$(basename "$f" .txt)
  TMP_BWT="$FINAL_DIR/${bn}.bwtsep.txt"
  TMP_MTF="$FINAL_DIR/${bn}.bwtmtf.txt"
  OUT_RLE="$FINAL_DIR/${bn}_bwtmtfrle.txt"

  if (( DO_BWT )); then
    python $MOD_DIR/crux2/crux2_bwt.py \
      --input "$f" \
      --output "$TMP_BWT" \
      --chunk-mode lines \
      --int-mode --int-sentinel -1
  fi
  if (( DO_MTF )); then
    python $MOD_DIR/crux2/crux2_mtf.py --input "$TMP_BWT" --output "$TMP_MTF" --alphabet_mode global
  fi
  if (( DO_RLE )); then
    python $MOD_DIR/crux2/crux2_rle.py --input "$TMP_MTF" --output "$OUT_RLE"
  fi

  # *** Final BWT over the RLE, treating as plain text (space-separated ints) ***
# CHUNKED FINAL BWT (prevent OOM on huge RLEs)
FINAL_BWT="$FINAL_DIR/${bn}_bwtmtfrle_bwt.txt"
TMP_SPLIT_PREFIX="$FINAL_DIR/${bn}_bwtmtfrle_chunk_"

# 1. Split the single line RLE file into lines of 10k tokens each
awk '
{
  n = split($0, a, " ");
  for (i = 1; i <= n; i += 10000) {
    out = "";
    for (j = i; j < i + 10000 && j <= n; ++j) {
      out = out a[j] " ";
    }
    print out > "'"$TMP_SPLIT_PREFIX"'" i ".txt";
  }
}
' "$OUT_RLE"

# 2. Run BWT per chunk, concat to final
> "$FINAL_BWT"
for chunk in ${TMP_SPLIT_PREFIX}*.txt; do
  python $MOD_DIR/crux2/crux2_bwt.py --input "$chunk" --output "${chunk}.bwt" --chunk-mode lines
  cat "${chunk}.bwt" >> "$FINAL_BWT"
  rm "${chunk}.bwt" "$chunk"
done

echo "[Luna] Chunked token-BWT completed: $FINAL_BWT"


  if (( CLEANUP_TMP )); then
    rm -f "$TMP_BWT" "$TMP_MTF"
  fi
done


#### [5] Dicts: flatten + BWT→MTF→RLE ===
DICT_IN_DIR="$CCNLP_OUT"
DICT_TMP_DIR="$OUTBASE/98_dicts_flat"
DICT_FINAL_DIR="$OUTBASE/99_dicts_final"
mkdir -p "$DICT_TMP_DIR" "$DICT_FINAL_DIR"

for dict in "$DICT_IN_DIR"/cat*_*.txt; do
  bn=$(basename "$dict" .txt)
  flat="$DICT_TMP_DIR/${bn}.flat.txt"
  chunked="$DICT_TMP_DIR/${bn}.chunked.txt"
  echo "[Luna] Flattening $dict -> $flat"
  tr '\n' ' ' < "$dict" | sed 's/ *$//' > "$flat"
  echo "[Luna] Chunking $flat -> $chunked"
  python modules/crux2/dict_flat_chunker.py "$flat" "$chunked"
done

if compgen -G "$DICT_TMP_DIR/*.flat.txt" > /dev/null; then
  echo "[Luna] Found dict flat files, proceeding with BWT/MTF/RLE."
else
  echo "[Luna] No dict flat files found in $DICT_TMP_DIR; skipping."
fi

for chunked in "$DICT_TMP_DIR"/*.chunked.txt; do
  [ -e "$chunked" ] || continue
  bn=$(basename "$chunked" .chunked.txt)
  bwt="$DICT_FINAL_DIR/${bn}.bwtsep.txt"
  mtf="$DICT_FINAL_DIR/${bn}.bwtmtf.txt"
  rle="$DICT_FINAL_DIR/${bn}_bwtmtfrle.txt"
  echo "[Luna] Processing $chunked → $rle"

  python $MOD_DIR/crux2/crux2_bwt.py --input "$chunked" --output "$bwt" --chunk-mode lines
  python $MOD_DIR/crux2/crux2_mtf.py --input "$bwt" --output "$mtf" --alphabet_mode global
  python $MOD_DIR/crux2/crux2_rle.py --input "$mtf" --output "$rle"

  # ---- Final robust BWT over huge single-line int files, chunk-safe ----
  finalbwt="$DICT_FINAL_DIR/${bn}_bwtmtfrle_bwt.txt"
  echo "[Luna] Final token-BWT (chunked, safe): $rle → $finalbwt"
  # 1. Split the giant line to N=10000-tokens-per-line temp file
  awk '
    {
      n = split($0, a, " ");
      for(i=1;i<=n;i++) {
        printf a[i];
        if(i<n) printf " ";
        if(i%10000==0) printf "\n";
      }
      printf "\n";
    }
  ' "$rle" > "${rle}.chunks"

  # 2. For each chunk-line, do BWT (Python, fast, RAM-safe)
  > "$finalbwt"
  while read -r line; do
    python3 -c "
tokens = [int(x) for x in '''$line'''.strip().split() if x]
if tokens:
    sent = -1
    seq = tokens + [sent]
    rot = [seq[i:]+seq[:i] for i in range(len(seq))]
    rot.sort()
    bwt = [str(row[-1]) for row in rot]
    print(' '.join(bwt))
" >> "$finalbwt"
  done < "${rle}.chunks"
  rm -f "${rle}.chunks"
done




  #### [6] Minimal Archive (final output) ####
  echo "=== [$BASENAME] [6] Compress for benchmarking (7z, minimal set) ==="
  7z a -mx=9 "$ARCHIVE" \
7z a -mx=9 "$ARCHIVE" \
  "$FINAL_DIR"/*_bwtmtfrle_bwt.txt \
  "$DICT_FINAL_DIR"/*_bwtmtfrle_bwt.txt \
  "$CODEBOOK_TXT"

    # "$CCNLP_OUT"/cat* \#bwtrle now

  #### [7] (Optional) Log Benchmark Results ####
  echo "=== [$BASENAME] [7] Log Benchmark Results ==="
  if [ -f "$MOD_DIR/core/bench_logger.py" ]; then
    python $MOD_DIR/core/bench_logger.py --indir "$FINAL_DIR" --out "$BENCH_LOG"
  else
    echo "[Luna] bench_logger.py not found, skipping benchmark log."
  fi

  echo "=== [$BASENAME] Pipeline finished successfully ==="
done
