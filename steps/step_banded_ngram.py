from pathlib import Path
import os
import numpy as np
from utils import ensure_dirs, run_python_module

def banded_ngram_pipeline(config, infile, ccnlp_out):
    """
    Multi-band n-gram aggregation/replacement/pruning (commons dicts only).
    Optimized for large datasets—aggregate n-grams over several passes,
    then replace/prune once at the end for memory efficiency.
    """
    from steps.step_03_replace_ngrams import step_replace_ngrams
    from modules.ngram_pos.dict_pruner import prune_commons_dict_and_save_mapping, remap_subidxs_with_mapping

    replaced_dir = f"{config['output_folder']}/{infile}/04_replaced"
    all_commons_dicts = list(Path(ccnlp_out).glob("cat*_commons.txt"))
    last_ngram_db = None

    # --- Loop over all ngram bands ---
    for pass_idx, band in enumerate(config['ngram_passes']):
        n_max = band['n_max']
        n_min = band['n_min']
        min_freq = band.get('min_freq', 2)
        start_code = band.get('start_code', config.get('start_code', 1000000))
        print(f"[Luna] [Banded] Pass {pass_idx+1}: n_max={n_max}, n_min={n_min}, min_freq={min_freq}")
        ngram = step_ngram_aggregate(config, infile, ccnlp_out, n_max, n_min, min_freq, start_code)
        last_ngram_db = ngram['ngrams_db']
        last_band = band  # <-- Capture for final replace

    # --- Final replacement & pruning ---
    print(f"[Luna] [Banded] Final n-gram replacement...")
    replace = step_replace_ngrams(
        config, infile, ccnlp_out, last_ngram_db,
        min_freq=last_band['min_freq'],
        start_code=last_band.get('start_code')
    )

    for dict_file in all_commons_dicts:
        pruned_dict = str(dict_file).replace(".txt", "_pruned.txt")
        mapping_file = str(dict_file).replace(".txt", "_mapping.txt")
        mapping = prune_commons_dict_and_save_mapping(
            replaced_dir=replaced_dir,
            orig_dict_path=dict_file,
            pruned_dict_path=pruned_dict,
            mapping_path=mapping_file
        )
        commons_len = sum(1 for _ in open(dict_file))
        remap_subidxs_with_mapping(replaced_dir, mapping, commons_len)

    print(f"[Luna] [Banded] All n-gram passes and pruning complete for {infile}")

def step_ngram_aggregate(config, infile, ccnlp_out, n_max, n_min, min_freq, start_code):
    modules_dir = config['modules_dir']
    output_folder = config['output_folder']
    ngrams_dir = os.path.join(output_folder, infile, "03_ngrams")
    ensure_dirs(ngrams_dir)
    script = os.path.join(modules_dir, "ngram_pos", "aggregate.py")  # Fix your module path if needed
    output_npz = os.path.join(ngrams_dir, "ngrams_dicts.npz")
    output_db = os.path.join(ngrams_dir, "ngrams_temp.db")
    args = {
        "indir": ccnlp_out,
        "pattern": "sub_idxs_*.npy",
        "n_max": n_max,
        "n_min": n_min,
        "min_freq": min_freq,
        "output": output_npz,
        "sqlite_db": output_db
    }
    run_python_module(script, args)
    return {"ngrams_dir": ngrams_dir, "ngrams_db": output_db, "ngrams_npz": output_npz}
