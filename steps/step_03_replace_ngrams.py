from utils import run_python_module, ensure_dirs, flatten_file_with_sentinel
import os

def step_replace_ngrams(config, infile, ccnlp_out, ngrams_db, min_freq=None, start_code=None):
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
        "min_freq": min_freq if min_freq is not None else config['ngram_passes'][-1]['min_freq'],
        "start_code": start_code if start_code is not None else config.get('start_code', 1000000),
        "pattern": "sub_idxs_*.npy"
    }
    run_python_module(script, args)

    # Flatten codebook here (output as .flat.txt for later BWT etc)
    codebook_flat = codebook_txt.replace('.txt', '.flat.txt')
    sentinel = config.get("sentinel", "-1")
    flatten_file_with_sentinel(codebook_txt, codebook_flat, sentinel=sentinel)
    print(f"[Luna] Flattened codebook: {codebook_txt} → {codebook_flat}")

    return {
        "replaced_dir": replaced_dir,
        "codebook_txt": codebook_txt,
        "codebook_flat": codebook_flat,
        "codebook_npz": codebook_npz
    }
