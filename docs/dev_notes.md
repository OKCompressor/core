Roadmap

    DAG orchestrator (auto-pick best step)

    GA module for .base4

    crux1 wrapper (thin, fast, classic BWT)

    Benchmarks auto-logged to /output/bench/

    Document reverse pipeline scripts

    Add simple_2-gram step if >len than dict entry

    Bench and pLM modules drafts

Tag: v0.3-minimal-pipeline


---

## 2. **docs/dev_notes.md** (raw dev notes, philosophy, rants, warnings, context dumps)

---

```markdown
# Dev Notes & Philosophy

> **Warning:** This is a messy, in-progress, sometimes stream-of-consciousness log.  
> Approach with empathy for the dev (future-you).

---

### General Philosophy

- This repo is “backup-first” not “release-ready.”
- Fork, hack, or lurk at your own risk.
- Some submodules are private or WIP, not all code is open right now.
- If you’re interested in the Rust routines, or want a private alpha, reach out and maybe I’ll share.
- PRs welcome but bring patience!

---

## Contextual Notes & Rants

- Occasionally, Rust executables or binaries may be dropped in to speed up bottlenecks.
- No production support, no guarantees.
- Minimal archive set: keep only what’s needed for full reverse; you can regen intermediates.
- Implement/add the 2-grams to core!
- Prune the dicts after replace_ngrams usage.
- Focus next on the GA module for .base4.
- crux1 wrapper: thin, fast, don’t stall for “perfect.”
- Write “auto-pick smallest” logic as a reusable DAG node.

---

## Misc Pipeline Observations

- Best path yet:  
  dicts (8x cat*) not processed further after ccnlp  
  ngram_used_codebook.txt.7z  
  base4 → to be GA  
  subidx*.npy  
- BWT and other transforms in crux2 yielded negative results, probably due to capped hardware/dev box limits. Chunk 10k max to prevent Out Of Mem.

---

## Size/Benchmark Snapshots

- **enwik5 full pipe +7z:** 44.4 kB (runtime < 2 mins)
- **dumb.7z:** 39.7 kB  
- **enwik5 7z direct:** 33.1 kB  
- **pruned+2-grams:** 34.2–31.4 kB  
- **enwik6 full pipe:** 386 kB  
- **enwik6 dumb.7z:** 330.4 kB  
- **enwik6.7z:** 290.8 kB

---

## Code Markings

- Code marked with `[Luna]` has been done by AI with hard specs/human dev in the loop.

---

*Take a break. Your brain will be sharper after.*
