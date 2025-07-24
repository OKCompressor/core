from utils import run_python_module, ensure_dirs
import os

def step_replace_ngrams(config, infile, ccnlp_out, ngrams_db):
    modules_dir = config['modules_dir']
    output_folder = config['output_folder']
    replaced_dir = os.path.join(output_folder, infile, "04_replaced")
    ensure_dirs(replaced_dir)
    script = os.path.join(modules_dir, "ngram-pos", "replace_ngrams.py")
    codebook_txt = os.path.join(output_folder, infile, "03_ngrams", "ngram_used_codebook.txt")
    codebook_npz = os.path.join(output_folder, infile, "03_ngrams", "ngram_used_codebook.npz")
    args = {
        "input_dir": ccnlp_out,
        "output_dir": replaced_dir,
        "ngram_db": ngrams_db,
        "final_codebook_txt": codebook_txt,
        "final_codebook_npz": codebook_npz,
        "min_freq": config['ngram']['min_freq'],
        "start_code": config['ngram']['start_code'],
        "pattern": "sub_idxs_*.npy"
    }
    run_python_module(script, args)
    return {"replaced_dir": replaced_dir, "codebook_txt": codebook_txt, "codebook_npz": codebook_npz}
