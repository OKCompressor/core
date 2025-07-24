from utils import run_python_module, ensure_dirs
import os
import glob

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
        # Flatten to one line (spaces)
        with open(dict_file) as f, open(flat, "w") as out:
            out.write(' '.join(x.strip() for x in f if x.strip()))
        # Chunk to N tokens/line (use Python or a script, your call)
        run_python_module(os.path.join(modules_dir, "crux2", "dict_flat_chunker.py"),
            {"input": flat, "output": chunked})
    return {"dict_tmp_dir": dict_tmp_dir}
