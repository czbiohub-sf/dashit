# DASHit

DASHit is a software package to design guide RNAs for DASH experiments.

# Installing

# Designing guides

1. Run `crispr_sites` to find all candidate guide RNA sequences in your input FASTQ
2. *Optional* Run `crispr_sites` to generate on-target and off-target files
3. Run `dashit-reads-filter` to remove candidate gRNAs that have poor structure (homopolymer, dinucleotide repeats, hairpins), represent adapter sequences, hit off targets, or don't hit on-targets
4. Run `optimize_guides` to find the gRNAs that hit the largest number of reads in your input FASTQ

To see how your designed guides perform, score your reads

# Scoring reads
