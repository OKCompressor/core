> ⚠️ **disclaimer:**  
> This is a personal, R&D project—code is *raw*, modules come and go,  
> and half the repo is notes-to-self or just “backed up” to git.  
> Don’t expect pro docs, stable APIs, or code etiquette yet.  
>  
> Use, fork, remix, or rage-quit at will.  
> PRs are cool if you dare—just know what you’re getting into.  


# OKCompressor Core

Modular, open corpus compression for the LLM era.


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


---


### API Table: Inputs, Outputs, Entrypoints

(For doc/README clarity, keep current; add CLI/params as you finalize)
| Module     | Entrypoint/Script     | Input(s)              | Output(s)              | Notes                |
| ---------- | --------------------- | --------------------- | ---------------------- | -------------------- |
| dumb\_pre  | dumb\_pre.py / redumb | raw\.txt              | dict.txt, out.txt      | Baseline reversible  |
| cc\_nlp    | proc\_post.py         | dicts/                | .bwtmtf.txt, .meta.npz | Mocked crux postproc |
| ngram_pos  | aggregate.py          | .bwtmtf.txt           | .npz, .tsv             | N-gram sweep/agg     |
| cc\_nlp    | ngram\_analyzer.py    | .tsv                  | codebook.json          | Semantic grouping    |
| cc\_nlp    | replace\_ngrams.py    | ngram\_db, input\_dir | output\_dir            | N-gram replacement   |
| ngram-dawg | runner.py             | token files           | .edgelist, .order.npy  | DAWG build/export    |
| crux       | crux.py               | token streams         | transformed streams    | Custom & transforms  |
| core       | bench\_logger.py      | output\_dir           | .tsv/.json logs        | Benchmarking/summary |
| ...        | ...                   | ...                   | ...                    | ...                  |


---

## 🔧 Planned Modules (Roadmap/Insertion Points)

- **dumb_pre**  
  Baseline word-level reversible tokenizer and dictionary compressor (open, auditable reference layer for the stack).
- **crux**  
  Custom transforms: MTF, BWT, RLE, and experimental pipelines.
- **cc_nlp**  
  Main insertion for AI/NLP-powered transforms, including custom language models, context-aware tokenization, etc.
- **stego**  
  Steganography and watermarking layers.
- **mapper**  
  Symbol remapping, token conversion, and index management.
- **mDAWG**  
  Multi-level DAWG (Directed Acyclic Word Graph) for fast dictionary lookups.
- **nGPE**  
  *Next-Gen Prefix Encoding*—our custom method, beyond classic BPE/multitok.
- **ranking**  
  Token and symbol ranking modules, integrates with crux and cc_nlp.
- **entrop**  
  Entropy coding: hooks for rANS/ANS/constriction, etc. (low priority due to API hurdles).

## 🤖 **AI Main Insertion Points**

- `cc_nlp`:  
  - Custom NLP, context-driven categorization
  - Integration with LLMs or local models for auto tokenization, error correction, or even lossy “compression” if desired


---

🛠️ Luna’s Minimal, Reversible Pipeline v2

You want:

    dumb_pre → cc_nlp (category tokenization) → ngram_pos (replacement) → crux2 BWT+MTF+RLE → final 7z archive.

    Archive should only include the minimal files needed for a lossless reverse.

Pipeline Flow (With Files/Outputs)
1. Dumb Preprocessing

    Input: data/enwik6

    Output:

        output/enwik6/00_dumb/output.txt

        output/enwik6/00_dumb/dict.txt (needed for CC-NLP and final reverse, but can be regenerated from commons+uniqs if you want ultra-minimal)

2. CC-NLP Category Chunking

    Input: above outputs

    Output:

        output/enwik6/ccnlp/sub_idxs_*.npy (token IDs per chunk)

        output/enwik6/ccnlp/cats_*.base4 (category per token, packed)

        output/enwik6/ccnlp/cat{n}_commons.txt

        output/enwik6/ccnlp/cat{n}_uniqs.txt

3. N-gram Aggregation (Replacement)

    Input: sub_idxs_*.npy

    Output:

        output/enwik6/03_ngrams/ngrams_cc_temp.db (sqlite ngram db for lookup)

        output/enwik6/03_ngrams/ngrams_cc_dicts.npz (optional for stats)

4. N-gram Replacement (Codebook)

    Input:

        sub_idxs_*.npy

        ngram db

    Output:

        output/enwik6/04_replaced/repl_subidx_*.npy

        output/enwik6/03_ngrams/ngram_used_codebook.txt

        output/enwik6/03_ngrams/ngram_used_codebook.npz

5. BWT → MTF → RLE Chain

    Apply to each repl_subidx_*.npy (convert to text or uint stream as needed for crux2 scripts)

    Output:

        output/enwik6/04_replaced/repl_subidx_*_bwtmtfrle.txt

6. Archive for Distribution

    Minimal set for lossless decompress:

        repl_subidx_*_bwtmtfrle.txt

        cats_*.base4

        cat{n}_commons.txt

        cat{n}_uniqs.txt

        ngram_used_codebook.txt (or .npz)

    (If you’re aggressive, you don’t need to keep the original dict.txt or dumbed .txt—these can be reconstructed from the category dicts if your reverse logic is robust.)

Reverse (Decompression) Flow

    Decompress all files from 7z.

    RLE → MTF → BWT (reverse crux2 chain) on each repl_subidx_ file.*

    Use codebook to restore original subidx sequence.

    Use cats_*.base4 and cat{n}_commons/uniqs.txt to reconstruct original tokens.

    Join tokens to reconstruct the original file.






---

9. Summary TODO Checklist

Add modules repo downloader for all steps like in pipe.py _legacy

Use chunked files for archive if present, else flat

Keep naming consistent and minimal

Archive only what’s needed for full reverse (can always regen intermediates)

Write the “auto-pick smallest” logic as a reusable DAG node

Focus next on the GA module for .base4

crux1 wrapper: thin, fast, don’t stall for “perfect”

! implement/add the 2-grams to core !!
! Prune the dicts after the replace_ngrams usage

Document all of this in README/docs

Take a break. Your brain will be sharper after.

===

Best path yet:

dicts (8x cat*) not procced further after ccnlp
ngram_used_codebook.txt.7z
base4 --> to be GA 
subidx*.npy

BWT and other transforms in crux2 yielded negative results probly for capped hw limits on the dev box, like chunk 10k max to prevent Out Of Mem


**the following tables is w aggregates down to 3 only :: 

!!! needs updates after implement/add the 2-grams to core !!!

full pipe +7z:
enwik 5: 44,4 kB (44377 bytes)
runtime < 2 mins

dumb.7z:
39,7 kB (39667 bytes)

enwik5 directly on 7z:
33,1 kB (33057 bytes)

for pruned and 2-grams
34,2 kB (34250 bytes) ?? 31,4 kB (31439 bytes)

!TODO: needs assert reversability and prune uniqs 

---

enwik6:
full pipe 
386 kb

dumb.7z
dict.7z 75.8 + out_ids.7z 254.8 kb =
330.4 kb

enwik6.7z:
290,8 kB (290753 bytes)

---



---

*PS: Code marked with [Luna] has be done by AI with hard reqs/specs human dev in the loop


---

## Quickstart

Install dependencies:

```bash
# Python 3.11+ recommended; PyPy optional for speed
pip install -r requirements.txt
# Or, for max speed:
pypy3 -m pip install -r requirements.txt

# If using Rust modules (experimental, for redumb/rengrams):
cargo build --release

Run the pipeline:

cd core
python main.py config.yaml
# Or, for PyPy:
pypy3 main.py config.yaml

Outputs will appear in output/{your_corpus}/99_dicts_final/.

---

- **Tag as:**  
  `v0.3-minimal-pipeline`
- **Roadmap:**
    - DAG orchestrator (auto-pick best step)
    - GA module for .base4
    - crux1 wrapper (thin, fast, “classic” BWT)
    - Empirical benchmarks auto-logged to /output/bench/
    - Document reverse pipeline scripts as they land

    - Handle as simple_ 2-gram step if >len than dict entry
    - bench and pLM modules drafts

---

