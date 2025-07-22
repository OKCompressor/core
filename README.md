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





