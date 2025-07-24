from utils import run_python_module, ensure_dirs
import os

def step_ngram_aggregate(config, infile, ccnlp_out):
    modules_dir = config['modules_dir']
    output_folder = config['output_folder']
    ngrams_dir = os.path.join(output_folder, infile, "03_ngrams")
    ensure_dirs(ngrams_dir)
    script = os.path.join(modules_dir, "ngram-pos", "aggregate.py")
    output_npz = os.path.join(ngrams_dir, "ngrams_dicts.npz")
    output_db = os.path.join(ngrams_dir, "ngrams_temp.db")
    args = {
        "indir": ccnlp_out,
        "pattern": "sub_idxs_*.npy",
        "n_max": config['ngram']['n_max'],
        "n_min": config['ngram']['n_min'],
        "output": output_npz,
        "sqlite_db": output_db
    }
    run_python_module(script, args)
    return {"ngrams_dir": ngrams_dir, "ngrams_db": output_db, "ngrams_npz": output_npz}
