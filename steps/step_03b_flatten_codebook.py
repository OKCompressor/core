from utils import flatten_file_with_sentinel, ensure_dirs
import os

def step_flatten_codebook(config, infile, codebook_txt):
    output_folder = config['output_folder']
    codebook_flat = os.path.join(output_folder, infile, "03_ngrams", "ngram_used_codebook.flat.txt")
    sentinel = config.get("sentinel", "\x00")  # or "-1" for ints
    flatten_file_with_sentinel(codebook_txt, codebook_flat, sentinel=sentinel)
    print(f"[Luna] Flattened codebook {codebook_txt} → {codebook_flat}")
    return {"codebook_flat": codebook_flat}
