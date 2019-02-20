# DASH analysis
`design_guides_wrapper.sh` illustrates a sample workflow for designing guides using DASHit. Arguments for the wrapper are your reads as fasta files, an on-target fasta and an off-target fasta. It will then create crispr sites files for your reads, your on-target fasta and your off-target fasta, and use the dashit_reads_filter.py Python script located in dashit/dashit-reads/dashit_reads/ to remove guides found in your reads which hit the off-target fasta and only keep guides that hit your reads and the on-target fasta.

It will then run optimize_guides to determine the number of reads hit by each guide, and run score_guides on your original reads with the full guide set to see how much is DASHable. You may want to re-run score_guides with 96, 192, etc guides, to determine how much would be DASHable by a smaller number of guides. The optimize_guides output can be used to make an elbow plot to determine the optimal number.

### Installation
Copy your reads, your on-target fasta, and your off-target fasta into the contrib folder, after following installation for the `guide_design_tools` repo.

Note: if you choose to move the wrapper elsewhere, you will need to edit the path to the dashit_reads_filter.py script in the wrapper.

### Dependencies
Python (script will import pandas), DASHit

### File Requirements
You should subsample your reads to 100k (can use seqtk), adaptor trim your reads (can use cutadapt) and convert them to fasta (can use seqtk). You can use bedtools to help generate your on-target and off-target fastas. If you have a bed file annotating on-target regions, you can use `bedtools getfasta` to generate an on-target fasta. You can use that same bed file to mask regions of a fasta to generate an off-target fasta, using `bedtools maskfasta`, with the `-mc -` option.

Your fastas should contain no letters other than A, G, C, T or N. Lowercase letters should be converted to uppercase.

### Running the script

Use bash to run the script and follow with 3 arguments
1. the file prefix for all of your read fastas
2. the file name of your on-target fasta
3. the file name of your off-target fasta

```
bash design_guides_wrapper.sh cut-filt-85-98-90_sub100k_GI01 ontarget_mm10-rRNA_region_UPPERcase.fa masked_mm10_SC5314_genomes_UPPERcase.fa
```

### Your final guides/optimize_guides output file 
Your final guides CSV (`final_guides.csv`) will contain four components.
1. the guide sequence (site)
2. the site index 
3. Number of reads covered by site
4. Cumulative number of reads hit

You should use this file to generate an elbow plot, with guide sequence on the x-axis and number of reads covered by site/total reads hit on the y-axis.

### Your formatted score_guides output file
Your formatted CSV (`final_guides_scored.csv`) will contain five columns
1. Guide library
2. Your filename
3. Total Reads DASHed (hit by score_guides)
4. Total Reads in sample
5. Percent DASHed

This file will tell you how much of your library would be DASHed by the full guide set. Use the elbow plot to determine how many guides would be most effective and rerun score_guides.

### Other files created
Files with `crispr_sites.txt` will contain guide sequences in your reads, on-target or off-target fastas which will be compatible with optimize_guides. A txt file called `final_guides_scored.txt`  is generated containing score_guides output before it is formatted into a CSV.
