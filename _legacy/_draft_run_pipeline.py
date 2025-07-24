# run_pipeline.py - Luna-vetted: bash → Python (calls modules as subprocess)
import os, sys, subprocess, shutil, glob

# ===== CONFIG/Toggles =====
DO_BWT = True
DO_MTF = True
DO_RLE = True
CLEANUP_TMP = True
CHUNK_SIZE = 10000

MOD_DIR = "modules"
INPUT_FOLDER = "data"
INPUT_FILES = ["enwik6"]  # Edit as needed

os.makedirs(MOD_DIR, exist_ok=True)
os.makedirs(INPUT_FOLDER, exist_ok=True)

for entry in ["modules/", "output/", "data/"]:
    if not any(l.strip() == entry for l in open(".gitignore").readlines()):
        with open(".gitignore", "a") as f:
            f.write(entry + "\n")

repos = {
    "dumb_pre": "git@github.com:OKCompressor/dumb_pre.git",
    "redumb": "git@github.com:OKCompressor/redumb.git",
    "ngram-pos": "git@github.com:GreenIshHat/ngram-pos.git",
    "cc_nlp": "git@github.com:GreenIshHat/cc_nlp.git",
    "ngram-dawg": "git@github.com:GreenIshHat/ngram-dawg.git",
    "crux2": "git@github.com:GreenIshHat/crux2.git",
    "core": "git@github.com:OKCompressor/core.git"
}
for name, url in repos.items():
    if not os.path.isdir(f"{MOD_DIR}/{name}"):
        subprocess.run(["git", "clone", url, f"{MOD_DIR}/{name}"], check=True)

def run(cmd):
    print(f"[Luna] RUN: {' '.join(str(x) for x in cmd)}")
    subprocess.run(cmd, check=True)

def split_line_file(infile, outprefix, chunk_size=10000):
    # Splits a space-separated, single-line file into N tokens per line
    with open(infile) as f:
        tokens = f.read().strip().split()
    for i in range(0, len(tokens), chunk_size):
        chunk = tokens[i:i+chunk_size]
        with open(f"{outprefix}{i+1}.txt", "w") as out:
            out.write(' '.join(chunk) + "\n")

for INFILE in INPUT_FILES:
    INPATH = f"{INPUT_FOLDER}/{INFILE}"
    if not os.path.isfile(INPATH) and os.path.isfile(f"{INPATH}.txt"):
        INPATH += ".txt"
    if not os.path.isfile(INPATH):
        print(f"[ERROR] Input file '{INPATH}' (or .txt) not found in {INPUT_FOLDER}/")
        sys.exit(1)

    BASENAME = os.path.splitext(os.path.basename(INFILE))[0]
    OUTBASE = f"output/{BASENAME}"

    RAW_DIR = f"{OUTBASE}/00_dumb"
    NGRAMS_DIR = f"{OUTBASE}/03_ngrams"
    CCNLP_OUT = f"{OUTBASE}/ccnlp"
    FINAL_DIR = f"{OUTBASE}/99_final"
    DICT_TMP_DIR = f"{OUTBASE}/98_dicts_flat"
    DICT_FINAL_DIR = f"{OUTBASE}/99_dicts_final"

    for d in [RAW_DIR, NGRAMS_DIR, CCNLP_OUT, FINAL_DIR, DICT_TMP_DIR, DICT_FINAL_DIR]:
        os.makedirs(d, exist_ok=True)

    # [0] Preprocessing
    if os.path.isfile(f"{MOD_DIR}/dumb_pre/dumb_pre_v2.py"):
        run(["python", f"{MOD_DIR}/dumb_pre/dumb_pre_v2.py",
             "--input", INPATH,
             "--dict", f"{RAW_DIR}/dict.txt",
             "--out", f"{RAW_DIR}/output.txt"])
        PREV_OUT = f"{RAW_DIR}/output.txt"
    else:
        PREV_OUT = INPATH

    # [1] CC-NLP Chunking
    if os.path.isfile(f"{MOD_DIR}/cc_nlp/chunked_encode.py"):
        run(["python", f"{MOD_DIR}/cc_nlp/chunked_encode.py",
             "--dumb_path", RAW_DIR,
             "--dict_file", "dict.txt",
             "--pos_file", "output.txt",
             "--outdir", CCNLP_OUT,
             "--chunk_size", "1000000"])

    # [2] N-gram aggregation
    run(["python", f"{MOD_DIR}/ngram_pos/aggregate.py",
         "--indir", CCNLP_OUT,
         "--pattern", "sub_idxs_*.npy",
         "--n_max", "13", "--n_min", "3",
         "--output", f"{NGRAMS_DIR}/ngrams_dicts.npz",
         "--sqlite_db", f"{NGRAMS_DIR}/ngrams_temp.db"])

    # [3] Replace n-grams
    run(["python", f"{MOD_DIR}/ngram_pos/replace_ngrams.py",
         "--input_dir", CCNLP_OUT,
         "--output_dir", f"{OUTBASE}/04_replaced",
         "--ngram_db", f"{NGRAMS_DIR}/ngrams_temp.db",
         "--final_codebook_txt", f"{NGRAMS_DIR}/ngram_used_codebook.txt",
         "--final_codebook_npz", f"{NGRAMS_DIR}/ngram_used_codebook.npz",
         "--min_freq", "7", "--start_code", "1000000",
         "--pattern", "sub_idxs_*.npy"])

    # [4] BWT/MTF/RLE + chunked final BWT
    for f in glob.glob(f"{OUTBASE}/04_replaced/repl_sub_idxs_*.txt"):
        bn = os.path.splitext(os.path.basename(f))[0]
        TMP_BWT = f"{FINAL_DIR}/{bn}.bwtsep.txt"
        TMP_MTF = f"{FINAL_DIR}/{bn}.bwtmtf.txt"
        OUT_RLE = f"{FINAL_DIR}/{bn}_bwtmtfrle.txt"
        if DO_BWT:
            run(["python", f"{MOD_DIR}/crux2/crux2_bwt.py", "--input", f, "--output", TMP_BWT, "--chunk-mode", "lines", "--int-mode", "--int-sentinel", "-1"])
        if DO_MTF:
            run(["python", f"{MOD_DIR}/crux2/crux2_mtf.py", "--input", TMP_BWT, "--output", TMP_MTF, "--alphabet_mode", "global"])
        if DO_RLE:
            run(["python", f"{MOD_DIR}/crux2/crux2_rle.py", "--input", TMP_MTF, "--output", OUT_RLE])
        # chunked final BWT
        FINAL_BWT = f"{FINAL_DIR}/{bn}_bwtmtfrle_bwt.txt"
        TMP_SPLIT_PREFIX = f"{FINAL_DIR}/{bn}_bwtmtfrle_chunk_"
        split_line_file(OUT_RLE, TMP_SPLIT_PREFIX, CHUNK_SIZE)
        with open(FINAL_BWT, "w") as outbwt:
            for chunk in sorted(glob.glob(f"{TMP_SPLIT_PREFIX}*.txt")):
                run(["python", f"{MOD_DIR}/crux2/crux2_bwt.py", "--input", chunk, "--output", f"{chunk}.bwt", "--chunk-mode", "lines"])
                outbwt.write(open(f"{chunk}.bwt").read())
                os.remove(f"{chunk}.bwt")
                os.remove(chunk)

    # [5] Dicts: flatten + chunk + BWT/MTF/RLE + chunked final BWT
    for dictf in glob.glob(f"{CCNLP_OUT}/cat*_*.txt"):
        bn = os.path.splitext(os.path.basename(dictf))[0]
        flat = f"{DICT_TMP_DIR}/{bn}.flat.txt"
        chunked = f"{DICT_TMP_DIR}/{bn}.chunked.txt"
        # flatten
        with open(dictf) as fin, open(flat, "w") as fout:
            fout.write(' '.join([line.strip() for line in fin]) + "\n")
        # chunk (assuming dict_flat_chunker.py is a line chunker)
        run(["python", f"{MOD_DIR}/crux2/dict_flat_chunker.py", flat, chunked])
        bwt = f"{DICT_FINAL_DIR}/{bn}.bwtsep.txt"
        mtf = f"{DICT_FINAL_DIR}/{bn}.bwtmtf.txt"
        rle = f"{DICT_FINAL_DIR}/{bn}_bwtmtfrle.txt"
        run(["python", f"{MOD_DIR}/crux2/crux2_bwt.py", "--input", chunked, "--output", bwt, "--chunk-mode", "lines"])
        run(["python", f"{MOD_DIR}/crux2/crux2_mtf.py", "--input", bwt, "--output", mtf, "--alphabet_mode", "global"])
        run(["python", f"{MOD_DIR}/crux2/crux2_rle.py", "--input", mtf, "--output", rle])
        # chunked BWT final
        finalbwt = f"{DICT_FINAL_DIR}/{bn}_bwtmtfrle_bwt.txt"
        split_line_file(rle, f"{rle}.chunk_", CHUNK_SIZE)
        with open(finalbwt, "w") as outbwt:
            for chunk in sorted(glob.glob(f"{rle}.chunk_*.txt")):
                run(["python", f"{MOD_DIR}/crux2/crux2_bwt.py", "--input", chunk, "--output", f"{chunk}.bwt", "--chunk-mode", "lines"])
                outbwt.write(open(f"{chunk}.bwt").read())
                os.remove(f"{chunk}.bwt")
                os.remove(chunk)

    # [6] Minimal archive (7z)
    run([
        "7z", "a", "-mx=9", f"{OUTBASE}/compressed.7z",
        f"{FINAL_DIR}/*_bwtmtfrle_bwt.txt",
        f"{DICT_FINAL_DIR}/*_bwtmtfrle_bwt.txt",
        f"{NGRAMS_DIR}/ngram_used_codebook.txt"
    ])

    # [7] Log benchmark results (optional)
    bench_logger = f"{MOD_DIR}/core/bench_logger.py"
    if os.path.isfile(bench_logger):
        run(["python", bench_logger, "--indir", FINAL_DIR, "--out", f"{OUTBASE}/benchmarks.tsv"])

    print(f"=== [{BASENAME}] Pipeline finished successfully ===")
