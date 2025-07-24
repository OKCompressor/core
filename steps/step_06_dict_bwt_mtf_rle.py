# steps/step_06_dict_bwt_mtf_rle.py

from utils import run_python_module, ensure_dirs
import os
import glob
from tqdm import tqdm

def safe_bwt_input(file, chunk_size=10000):
    # If file is "flat" (one huge line) and large, split first
    with open(file) as f:
        lines = f.readlines()
    if len(lines) == 1 and len(lines[0].split()) > chunk_size:
        # Chunk it
        prefix = file.replace(".txt", "_chunked_")
        tokens = lines[0].strip().split()
        for i in range(0, len(tokens), chunk_size):
            chunk_file = f"{prefix}{i}.txt"
            with open(chunk_file, "w") as out:
                out.write(' '.join(tokens[i:i+chunk_size]) + "\n")
        # Return list of chunked files
        return [f"{prefix}{i}.txt" for i in range(0, len(tokens), chunk_size)]
    else:
        return [file]


def step_dict_bwt_mtf_rle(config, infile, dict_tmp_dir_or_file):
    """
    Runs BWT/MTF/RLE on all chunked files in a directory, or a single file.
    Returns dict_final_dir and (optionally) output file paths for direct input.
    """
    modules_dir = config['modules_dir']
    output_folder = config['output_folder']
    dict_final_dir = os.path.join(output_folder, infile, "99_dicts_final")
    ensure_dirs(dict_final_dir)

    # Accept both a directory of chunked files or a single flat file
    if os.path.isdir(dict_tmp_dir_or_file):
        files = glob.glob(os.path.join(dict_tmp_dir_or_file, "*.chunked.txt"))
    elif os.path.isfile(dict_tmp_dir_or_file):
        files = [dict_tmp_dir_or_file]
    else:
        print(f"[Luna] Input not found: {dict_tmp_dir_or_file}")
        return {"dict_final_dir": dict_final_dir}

    out_files = []

    for chunked in tqdm(files, desc="[Luna] BWT/MTF/RLE files"):
        # Support both ".chunked.txt" and ".flat.txt" input
        bn = os.path.basename(chunked)
        if bn.endswith(".chunked.txt"):
            bn = bn[:-12]
        elif bn.endswith(".flat.txt"):
            bn = bn[:-9]
        else:
            bn = bn.split('.')[0]

        bwt = os.path.join(dict_final_dir, f"{bn}.bwtsep.txt")
        mtf = os.path.join(dict_final_dir, f"{bn}.bwtmtf.txt")
        rle = os.path.join(dict_final_dir, f"{bn}_bwtmtfrle.txt")
        run_python_module(os.path.join(modules_dir, "crux2", "crux2_bwt.py"),
            {"input": chunked, "output": bwt, "chunk-mode": "lines"})
        run_python_module(os.path.join(modules_dir, "crux2", "crux2_mtf.py"),
            {"input": bwt, "output": mtf, "alphabet_mode": "global"})
        run_python_module(os.path.join(modules_dir, "crux2", "crux2_rle.py"),
            {"input": mtf, "output": rle})
        out_files.append(rle)

        # --- After your out_files.append(rle)
        # Add final _bwt always, but chunk first if needed!
        bwt_inputs = safe_bwt_input(rle)  # This returns a list: either [rle] or list of chunked files

        for bwt_input in bwt_inputs:
            # Generate output name for each chunk (or original)
            if bwt_input == rle:
                final_bwt = rle.replace(".txt", "_bwt.txt")
            else:
                base = os.path.basename(bwt_input).replace(".txt", "")
                final_bwt = os.path.join(dict_final_dir, f"{base}_bwt.txt")
            run_python_module(
                os.path.join(modules_dir, "crux2", "crux2_bwt.py"),
                {"input": bwt_input, "output": final_bwt, "chunk-mode": "lines"}
            )


    # If called with a codebook, return the output RLE file as 'codebook_flat'
    if len(out_files) == 1 and out_files[0].endswith("_bwtmtfrle.txt"):
        final_bwt_file = out_files[0].replace(".txt", "_bwt.txt")
        return {
            "dict_final_dir": dict_final_dir,
            "codebook_flat": out_files[0],
            "codebook_bwt": final_bwt_file
        }
    else:
        return {"dict_final_dir": dict_final_dir}
