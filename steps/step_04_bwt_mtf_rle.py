from utils import run_python_module, ensure_dirs, split_line_file
import os
import glob

def step_bwt_mtf_rle(config, infile, replaced_dir):
    modules_dir = config['modules_dir']
    output_folder = config['output_folder']
    final_dir = os.path.join(output_folder, infile, "99_final")
    ensure_dirs(final_dir)
    for f in glob.glob(os.path.join(replaced_dir, "repl_sub_idxs_*.txt")):
        bn = os.path.basename(f)[:-4]
        tmp_bwt = os.path.join(final_dir, f"{bn}.bwtsep.txt")
        tmp_mtf = os.path.join(final_dir, f"{bn}.bwtmtf.txt")
        out_rle = os.path.join(final_dir, f"{bn}_bwtmtfrle.txt")
        # 1. BWT
        run_python_module(os.path.join(modules_dir, "crux2", "crux2_bwt.py"),
            {"input": f, "output": tmp_bwt, "chunk-mode": "lines", "int-mode": True, "int-sentinel": -1})
        # 2. MTF
        run_python_module(os.path.join(modules_dir, "crux2", "crux2_mtf.py"),
            {"input": tmp_bwt, "output": tmp_mtf, "alphabet_mode": "global"})
        # 3. RLE
        run_python_module(os.path.join(modules_dir, "crux2", "crux2_rle.py"),
            {"input": tmp_mtf, "output": out_rle})
        # 4. Final token-BWT (chunked, RAM safe)
        final_bwt = os.path.join(final_dir, f"{bn}_bwtmtfrle_bwt.txt")
        split_line_file(out_rle, os.path.join(final_dir, f"{bn}_bwtmtfrle_chunk_"))
        # For each chunk, BWT and append (chunking func already in utils)
        chunk_files = glob.glob(os.path.join(final_dir, f"{bn}_bwtmtfrle_chunk_*.txt"))
        with open(final_bwt, "w") as fout:
            for chunk in chunk_files:
                run_python_module(os.path.join(modules_dir, "crux2", "crux2_bwt.py"),
                    {"input": chunk, "output": chunk + ".bwt", "chunk-mode": "lines"})
                with open(chunk + ".bwt") as fin:
                    fout.write(fin.read())
                os.remove(chunk)
                os.remove(chunk + ".bwt")
    return {"final_dir": final_dir}
