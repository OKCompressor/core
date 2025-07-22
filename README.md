# OKCompressor Core

Modular, open corpus compression for the LLM era.


	/OKCompressor
	  /core           # Orchestration, main scripts, API/readme, entrypoint
	  /dumb_pre       # Baseline reversible word tokenization/dicts
	  /redumb         # Rust-based, WIP, dumb_pre
	  /ngram-pos      # N-gram positional tools
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
| ngram-pos  | aggregate.py          | .bwtmtf.txt           | .npz, .tsv             | N-gram sweep/agg     |
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

    dumb_pre → cc_nlp (category tokenization) → ngram-pos (replacement) → crux2 BWT+MTF+RLE → final 7z archive.

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



