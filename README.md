# OKCompressor Core

> ⚠️ **dev/scene disclaimer:**  
> This is a personal, in-progress R&D compression playground.  
> Code, modules, and docs are **messy**, **fluid**, and often “notes to self.”  
> Some submodules are private, drafts or WIP (experimental)—not all code is open right now.  
> Occasionally, Rust executables or binaries may be dropped in to speed up bottlenecks.  
> No production support, no guarantees—this repo is “backup-first,” not “release-ready.”  
> Fork, hack, or lurk at your own risk. PRs welcome but bring patience!

---

## Modular, open corpus compression for the LLM era.

### Directory Structure
<details>
<summary><strong>Click to expand project tree</strong></summary>

	/OKCompressor
	  /core           # Orchestration, main scripts, API/readme, entrypoint
   
	  /dumb_pre       # Baseline reversible word tokenization/dicts
	  /redumb         # Rust-based, WIP, dumb_pre
   
	  /ngram_pos      # N-gram positional tools
	  /cc_nlp         # NLP & AI transforms, DAWG, codebook
		/ngram-dawg     # Modular DAWG & automata toolkit
		/rengrams       # Rust n-grams/faster routines
	
	  /crux           # Custom compression transforms (BWT, MTF, etc.)
	
	  /stego          # Steganography/watermarking layers (R&D)
	  /mapper         # Symbol remapping, index management
	  /cypher	  # pgp, aes per file/block for now. cc_PQC later. FHE.
	
		/mDAWG          # Multi-level DAWG
		/nGPE           # Next-gen prefix encoding (future/experimental)
	
	  /ranking        # Token/symbol ranking modules
	
	  /entrop         # Entropy coding: rANS/ANS/constriction hooks
	
	
	* /pLM 		  # pseudo LM, statistical word models from the ngrams of OKC

</details>

---

### API Table: Inputs, Outputs, Entrypoints

| Module     | Entrypoint/Script     | Input(s)              | Output(s)              | Notes                |
| ---------- | --------------------- | --------------------- | ---------------------- | -------------------- |
| dumb_pre   | dumb_pre.py / redumb  | raw.txt               | dict.txt, out.txt      | Baseline reversible  |
| cc_nlp     | proc_post.py          | dicts/                | .bwtmtf.txt, .meta.npz | Mocked crux postproc |
| ngram_pos  | aggregate.py          | .bwtmtf.txt           | .npz, .tsv             | N-gram sweep/agg     |
| cc_nlp     | ngram_analyzer.py     | .tsv                  | codebook.json          | Semantic grouping    |
| cc_nlp     | replace_ngrams.py     | ngram_db, input_dir   | output_dir             | N-gram replacement   |
| ngram-dawg | runner.py             | token files           | .edgelist, .order.npy  | DAWG build/export    |
| crux       | crux.py               | token streams         | transformed streams    | Custom & transforms  |
| core       | bench_logger.py       | output_dir            | .tsv/.json logs        | Benchmarking/summary|
| ...        | ...                   | ...                   | ...                    | ...                  |

---

## Minimal, Reversible Pipeline (v0.3-minimal-pipeline)

**Core flow:**

```text
dumb_pre → cc_nlp (category tokenization) → ngram_pos (replacement) → crux2 BWT+MTF+RLE → final 7z archive.

    Archive should only include minimal files for lossless reverse.

Pipeline Stages

    Dumb Preprocessing:

        Input: data/enwik6

        Output: output/enwik6/00_dumb/output.txt, dict.txt

    CC-NLP Category Chunking:

        Output: sub_idxs_*.npy, cats_*.base4, cat{n}_commons.txt, cat{n}_uniqs.txt

    N-gram Aggregation (Replacement):

        Output: ngrams_cc_temp.db, ngrams_cc_dicts.npz

    N-gram Replacement (Codebook):

        Output: repl_subidx_*.npy, ngram_used_codebook.txt/.npz

    BWT → MTF → RLE Chain:

        Output: repl_subidx_*_bwtmtfrle.txt

    Minimal Archive Set for Decompression:

        repl_subidx_*_bwtmtfrle.txt, cats_*.base4, cat{n}_commons.txt, cat{n}_uniqs.txt, ngram_used_codebook.txt/.npz

Reverse:
Unarchive → RLE → MTF → BWT reverse → codebook restore → category dicts → join tokens → original file.
```


### Quickstart

	# Python 3.11+ recommended; PyPy optional for speed
	pip install -r requirements.txt
	# Or, for max speed:
	pypy3 -m pip install -r requirements.txt
	
	# If using Rust modules (experimental, for redumb/rengrams):
	cargo build --release
	
	cd core
	python main.py config.yaml
	# Or, for PyPy:
	pypy3 main.py config.yaml
	
	# Outputs: output/{your_corpus}/99_dicts_final/
