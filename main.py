import sys
import os

from utils import load_config
from steps.step_00_dumb_pre import step_dumb_pre
from steps.step_01_ccnlp_chunk import step_ccnlp_chunk
from steps.step_02_ngram_aggregate import step_ngram_aggregate
from steps.step_03_replace_ngrams import step_replace_ngrams
from steps.step_03b_flatten_codebook import step_flatten_codebook
from steps.step_04_subidx_bwt import process_subidxs_through_bwt
from steps.step_05_dict_flatten_chunk import step_dict_flatten_chunk
from steps.step_06_dict_bwt_mtf_rle import step_dict_bwt_mtf_rle
from steps.step_07_archive import step_archive
from steps.step_08_bench_log import step_bench_log


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    config = load_config(config_path)
    for infile in config['input_files']:
        print(f"=== [{infile}] Step 0: Dumb Pre ===")
        dumb = step_dumb_pre(config, infile)
        print(f"=== [{infile}] Step 1: CC-NLP Chunking ===")
        ccnlp = step_ccnlp_chunk(config, infile, dumb['raw_dir'])
        print(f"=== [{infile}] Step 2: N-gram Aggregate ===")
        ngram = step_ngram_aggregate(config, infile, ccnlp['ccnlp_out'])
        
        print(f"=== [{infile}] Step 3: Replace N-grams ===")
        replace = step_replace_ngrams(config, infile, ccnlp['ccnlp_out'], ngram['ngrams_db'])
        flatten = step_flatten_codebook(config, infile, replace['codebook_txt'])
 
        print(f"=== [{infile}] Step 4: BWT/MTF/RLE (subidx) ===")
        bwt = step_dict_bwt_mtf_rle(config, infile, replace['replaced_dir'])

        print(f"=== [{infile}] Step 4b: BWT/MTF/RLE (subidxs from 04_replaced) ===")
        subidx_bwt_files = process_subidxs_through_bwt(config, infile)

        print(f"=== [{infile}] Step 5: Dict Flatten/Chunk ===")
        dict_flat = step_dict_flatten_chunk(config, infile)

        print(f"=== [{infile}] Step 6: Dict BWT/MTF/RLE (dicts) ===")
        dict_bwt = step_dict_bwt_mtf_rle(config, infile, dict_flat['dict_tmp_dir'])

        print(f"=== [{infile}] Step 6b: Dict BWT/MTF/RLE (codebook) ===")
        dict_bwt_codebook = step_dict_bwt_mtf_rle(config, infile, flatten['codebook_flat'])
        
        print(f"[Luna] Codebook BWT/MTF/RLE output: {dict_bwt_codebook.get('codebook_flat')}")

        archive = step_archive(
            config,
            infile,
            bwt['dict_final_dir'],
            dict_bwt['dict_final_dir'],
            dict_bwt_codebook['codebook_bwt'],    
            subidx_bwt_files
        )

        print(f"=== [{infile}] Step 8: Benchmark Log ===")
        bench = step_bench_log(config, infile, bwt['dict_final_dir']) # <<<<<
        print(f"=== [{infile}] Pipeline finished for [{infile}] ===")

if __name__ == "__main__":
    main()

