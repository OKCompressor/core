250724:

5. Ngram Analyzer (optional, but cool)

    Module that:

        Takes all dicts/subidxs and outputs per-token frequencies (histograms, Zipf curve, knee, etc).

        Super useful for tuning thresholds and visualizing compression power.

6. Final Archive Structure

    Archive:

        Pruned cat_commons.txt, cat_uniqs.txt

        All mapping files (for audit/debug)

        Final subidxs (after all remaps)

        Final ngram codebook

        (Optionally) base4-packed subidxs

        Compression logs & stats

    Omit raw BWT/MTF etc for now; focus on the minimal, lossless set!


***

last resort:
ditch the replacer -> pruner. rebuilt new dumb runs.