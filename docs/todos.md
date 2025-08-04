# TODOs

- [ ] Add modules repo downloader for all steps (as in pipe.py _legacy)
- [ ] Use chunked files for archive if present, else flat
- [ ] Keep naming consistent and minimal
- [ ] Archive only what’s needed for full reverse (regen intermediates as needed)
- [ ] Write “auto-pick smallest” logic as a reusable DAG node
- [ ] Focus on the GA module for .base4 next
- [ ] Implement crux1 wrapper (thin, fast, classic BWT—don’t stall for “perfect”)
- [ ] **Implement/add the 2-grams to core**
- [ ] Prune dicts after replace_ngrams usage
- [ ] Assert reversibility and prune uniqs
- [ ] Document all of this in README/docs
- [ ] Bench and pLM module drafts
- [ ] Empirical benchmarks auto-logged to /output/bench/
- [ ] Document reverse pipeline scripts as they land
- [ ] Handle as simple_2-gram step if >len than dict entry

---

## Known Issues

- [ ] BWT and other transforms in crux2 yielded negative results (likely due to dev box hw limits—chunk to 10k max)
- [ ] Needs update after 2-gram integration

