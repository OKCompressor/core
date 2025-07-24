from utils import run_python_module, ensure_dirs, flatten_file_with_sentinel
import os
import glob
import subprocess

def step_flatten_codebook(config, infile, outfile):
    """
    Flattens a codebook or dict file to a single line with a sentinel between lines.
    """
    sentinel = config.get("sentinel", "\x00")  # Can be "\x00" for char, or "-1" for ints
    flatten_file_with_sentinel(infile, outfile, sentinel)
    print(f"[Luna] Flattened {infile} to {outfile} with sentinel {repr(sentinel)}")

def step_dict_flatten_chunk(config, infile):
    modules_dir = config['modules_dir']
    output_folder = config['output_folder']
    ccnlp_out = os.path.join(output_folder, infile, "ccnlp")
    dict_tmp_dir = os.path.join(output_folder, infile, "98_dicts_flat")
    ensure_dirs(dict_tmp_dir)

    for dict_file in glob.glob(os.path.join(ccnlp_out, "cat*_*.txt")):
        bn = os.path.basename(dict_file)[:-4]
        flat = os.path.join(dict_tmp_dir, f"{bn}.flat.txt")
        chunked = os.path.join(dict_tmp_dir, f"{bn}.chunked.txt")
        # Use flatten_file_with_sentinel (modular!)
        sentinel = config.get("sentinel", "-1")
        flatten_file_with_sentinel(dict_file, flat, sentinel=sentinel)
        # Now chunk to N tokens/line (calls your chunker, could be in utils or a python script)
        subprocess.run([
            "python", os.path.join(modules_dir, "crux2", "dict_flat_chunker.py"),
            flat, chunked
        ], check=True)
        print(f"[Luna] Flattened and chunked {dict_file} → {chunked}")

    return {"dict_tmp_dir": dict_tmp_dir}
