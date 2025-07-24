from utils import run_python_module, ensure_dirs
import os

def step_ccnlp_chunk(config, infile, raw_dir):
    modules_dir = config['modules_dir']
    output_folder = config['output_folder']
    ccnlp_out = os.path.join(output_folder, infile, "ccnlp")
    ensure_dirs(ccnlp_out)
    script = os.path.join(modules_dir, "cc_nlp", "chunked_encode.py")
    args = {
        "dumb_path": raw_dir,
        "dict_file": "dict.txt",
        "pos_file": "output.txt",
        "outdir": ccnlp_out,
        "chunk_size": config['chunk_size']
    }
    run_python_module(script, args)
    return {"ccnlp_out": ccnlp_out}
