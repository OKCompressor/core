#!/usr/bin/env python3
# OKCompressor Modular Pipeline Runner
# python run_pipeline.py --inputs enwik5 enwik6 --preprocessor dumb_pre

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
import logging
import datetime
import json

# ==== CONFIG ====
REPOS = {
    "dumb_pre":      "https://github.com/OKCompressor/dumb_pre",
    "redumb":        "https://github.com/OKCompressor/redumb",
    "ngram-pos":     "https://github.com/GreenIshHat/ngram-pos",
    "cc_nlp":        "https://github.com/GreenIshHat/cc_nlp",
    "ngram-dawg":    "https://github.com/GreenIshHat/ngram-dawg",
    "core":          "https://github.com/OKCompressor/core"
}
PIPELINE_STAGES = [
    "preprocess",
    "bwt_mtf",
    "ngram_agg",
    "ngram_analyze",
    "replace_ngrams",
    "priv_cc_encode",   # Private, skip if not enabled
    "dawg_build",
    "compress",
    "bench_log"
]
DEFAULT_INPUTS = ["enwik5", "enwik6"] # Expand as needed

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# ==== UTILS ====
def run(cmd, **kwargs):
    """Run a shell command and echo, exit on error."""
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")
    return result

def clone_repo(name, url):
    if not os.path.exists(name):
        print(f"Cloning {name}...")
        run(f"git clone {url} {name}")

def log_result(log_path, data):
    with open(log_path, "a") as f:
        f.write(json.dumps(data) + "\n")

def assert_roundtrip(original_file, restored_file):
    """Placeholder: implement actual file comparison/assertion logic."""
    if not os.path.exists(restored_file):
        raise FileNotFoundError(f"Roundtrip failed: {restored_file} missing")
    # You can do file hash compare, diff, or your own logic
    with open(original_file, "rb") as f1, open(restored_file, "rb") as f2:
        if f1.read() != f2.read():
            raise AssertionError(f"Roundtrip failed: {original_file} != {restored_file}")

# ==== PIPELINE STAGES ====
def stage_preprocess(args, infile, outdir):
    """Choose dumb_pre or redumb based on param."""
    # TODO: Adjust CLI as per your module!
    preproc = args.preprocessor
    outdict = os.path.join(outdir, f"{infile}_dict.txt")
    outtxt  = os.path.join(outdir, f"{infile}_output.txt")
    if preproc == "dumb_pre":
        run(f"python dumb_pre/dumb_pre.py --input {infile} --dict {outdict} --out {outtxt}")
    elif preproc == "redumb":
        run(f"./redumb/redumb --input {infile} --dict {outdict} --out {outtxt}")
    else:
        raise ValueError("Unknown preprocessor")
    # Return main out path(s)
    return outdict, outtxt

def stage_bwt_mtf(args, dictfile, outdir):
    run(f"python cc_nlp/proc_post.py --input {dictfile} --output {outdir}")

def stage_ngram_agg(args, indir):
    run(f"python ngram-pos/aggregate.py --indir {indir} --mode nsweep --n_max 9 --n_min 4 --min_freq 3 --output ngrams_dicts.npz")

def stage_ngram_analyze(args):
    run(f"python cc_nlp/ngram_analyzer.py --freqs ngrams_dicts.tsv --out codebook.json --split-mode elbow --edit-cluster")

def stage_replace_ngrams(args, indir, outdir):
    run(f"python cc_nlp/replace_ngrams.py --ngram_db ngrams_temp.db --input_dir {indir} --output_dir {outdir}")

def stage_priv_cc_encode(args, indir, outdir):
    if not args.run_priv_cc:
        print("[INFO] Skipping proprietary CC encoding (not enabled)")
        return
    # Placeholder: run private/proprietary module (binary, Rust, etc.)
    print("[PRIV] Running CC encoding (private, not released)")
    # run(f"./crux/cc_encode ...") # If exists
    # For now, just copy through
    shutil.copytree(indir, outdir, dirs_exist_ok=True)

def stage_dawg_build(args, indir, outdir):
    run(f"python ngram-dawg/runner.py --input {indir} --outdir {outdir}")

def stage_compress(args, indir, outzip):
    run(f"7z a -mx=9 {outzip} {indir}/*")

def stage_bench_log(args, indir, logpath):
    run(f"python core/bench_logger.py --indir {indir} --out {logpath}")

# ==== MAIN ====
def main():
    parser = argparse.ArgumentParser(description="OKCompressor Modular Pipeline Runner")
    parser.add_argument("--inputs", nargs="+", default=DEFAULT_INPUTS, help="Input files/corpora")
    parser.add_argument("--outdir", default="output_pipeline", help="Main output dir")
    parser.add_argument("--preprocessor", choices=["dumb_pre", "redumb"], default="dumb_pre")
    parser.add_argument("--run-priv-cc", action="store_true", help="Run proprietary CC encoding stage (if enabled)")
    parser.add_argument("--skip-clone", action="store_true", help="Skip auto-clone of repos")
    parser.add_argument("--benchlog", default="benchmarks.tsv", help="Benchmark output file")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    os.chdir(args.outdir)

    # ==== Clone repos if needed ====
    if not args.skip_clone:
        for repo, url in REPOS.items():
            clone_repo(repo, url)

    # ==== For each input file/corpus ====
    for infile in args.inputs:
        logging.info(f"==== Processing: {infile} ====")
        step_dir = Path(f"{infile}_proc")
        step_dir.mkdir(exist_ok=True)
        orig_path = f"../{infile}" if not os.path.exists(infile) else infile

        # 1. Preprocess (dumb_pre/redumb)
        dict_path, outtxt_path = stage_preprocess(args, orig_path, step_dir)

        # 2. BWT+MTF transform
        bwt_dir = step_dir / "bwt_mtf"
        bwt_dir.mkdir(exist_ok=True)
        stage_bwt_mtf(args, dict_path, bwt_dir)

        # 3. N-gram Aggregation
        agg_dir = bwt_dir
        stage_ngram_agg(args, agg_dir)

        # 4. N-gram Analyzer
        stage_ngram_analyze(args)

        # 5. Replace n-grams with codebook
        replaced_dir = step_dir / "replaced"
        replaced_dir.mkdir(exist_ok=True)
        stage_replace_ngrams(args, bwt_dir, replaced_dir)

        # 6. (Optional/Private) CC Encode
        priv_dir = step_dir / "priv_cc"
        priv_dir.mkdir(exist_ok=True)
        stage_priv_cc_encode(args, replaced_dir, priv_dir)

        # 7. DAWG Build (optional)
        dawg_dir = step_dir / "dawg"
        dawg_dir.mkdir(exist_ok=True)
        stage_dawg_build(args, replaced_dir, dawg_dir)

        # 8. Compression (7z)
        outzip = f"{step_dir}/compressed.7z"
        stage_compress(args, replaced_dir, outzip)

        # 9. Benchmark logging
        log_path = step_dir / args.benchlog
        stage_bench_log(args, replaced_dir, log_path)

        # 10. Roundtrip Assert (TODO: Implement properly for your data)
        # assert_roundtrip(orig_path, restored_path) # You will need to define this

        logging.info(f"==== Finished {infile} ====")

    logging.info("Pipeline finished for all inputs.")

if __name__ == "__main__":
    main()
