import sys
from pathlib import Path

from utils import load_config
from steps.step_00_dumb_pre import step_dumb_pre
from steps.step_01_ccnlp_chunk import step_ccnlp_chunk
from steps.step_banded_ngram import banded_ngram_pipeline, step_ngram_aggregate 

from steps.step_07_archive import step_archive  # <- We’ll edit this

def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    config = load_config(config_path)

    for infile in config['input_files']:
        print(f"=== [{infile}] Step 0: Dumb Pre ===")
        dumb = step_dumb_pre(config, infile)

        print(f"=== [{infile}] Step 1: CC-NLP Chunking ===")
        ccnlp = step_ccnlp_chunk(config, infile, dumb['raw_dir'])

        print(f"=== [{infile}] Step 2-3: Banded N-gram Agg+Replace+Prune ===")
        banded_ngram_pipeline(config, infile, ccnlp['ccnlp_out'])

        print(f"=== [{infile}] Step 7: Archive Output Artifacts ===")
        # Gather files to archive:
        out_dir = f"{config['output_folder']}/{infile}"
        codebook_dir = f"{out_dir}/03_ngrams"
        replaced_dir = f"{out_dir}/04_replaced"
        ccnlp_out = ccnlp['ccnlp_out']

        # Find pruned commons dicts and mapping files
        pruned_commons = list(Path(ccnlp_out).glob("cat*_commons_pruned.txt"))
        mapping_files  = list(Path(ccnlp_out).glob("cat*_commons_mapping.txt"))
        # Optionally, grab the last codebook
        codebook_files = list(Path(codebook_dir).glob("ngram_used_codebook*"))
        # Subidxs pruned (after remap)
        pruned_subidxs = list(Path(replaced_dir).glob("sub_idxs_*.npy"))
        # Base4 cat arrays
        base4_files = list(Path(ccnlp_out).glob("cats_*.base4"))

        # Meta/info files (add as needed)
        # meta_files = [...]

        files_to_archive = pruned_commons + mapping_files + codebook_files + pruned_subidxs + base4_files # + meta_files

        # Archive: Provide output archive path
        archive_path = f"{out_dir}/compressed.7z"
        step_archive(files_to_archive, archive_path)

        print(f"=== [{infile}] Pipeline finished for [{infile}] ===")

if __name__ == "__main__":
    main()
