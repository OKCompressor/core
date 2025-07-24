from utils import run_python_module, ensure_dirs
import os
import glob

def step_dict_bwt_mtf_rle(config, infile, dict_tmp_dir):
    modules_dir = config['modules_dir']
    output_folder = config['output_folder']
    dict_final_dir = os.path.join(output_folder, infile, "99_dicts_final")
    ensure_dirs(dict_final_dir)
    for chunked in glob.glob(os.path.join(dict_tmp_dir, "*.chunked.txt")):
        bn = os.path.basename(chunked)[:-12]
        bwt = os.path.join(dict_final_dir, f"{bn}.bwtsep.txt")
        mtf = os.path.join(dict_final_dir, f"{bn}.bwtmtf.txt")
        rle = os.path.join(dict_final_dir, f"{bn}_bwtmtfrle.txt")
        run_python_module(os.path.join(modules_dir, "crux2", "crux2_bwt.py"),
            {"input": chunked, "output": bwt, "chunk-mode": "lines"})
        run_python_module(os.path.join(modules_dir, "crux2", "crux2_mtf.py"),
            {"input": bwt, "output": mtf, "alphabet_mode": "global"})
        run_python_module(os.path.join(modules_dir, "crux2", "crux2_rle.py"),
            {"input": mtf, "output": rle})
        # (Same chunked BWT logic as before—repeat or factor into utils if needed)
    return {"dict_final_dir": dict_final_dir}
