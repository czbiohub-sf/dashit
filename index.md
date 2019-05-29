# DASHit

DASHit is a software package to design guide RNAs for DASH experiments.

# Installing

DASHit runs on macOS and Linux (it's likely DASHit will compile on Windows, but we haven't tested this!). To install DASHit, you'll need:

## Dependencies

1. [go|https://www.golang.org]
   Note: `brew install golang`, `nix-env -i go`
2. [Python 3.7|https://www.python.org/]
   Note: `brew install`

## Installing DASHit
1. Install the Biohub's [`special_ops_crispr_tools`|https://www.github.com/czbiohub/special_ops_crispr_tools/]
   ```bash
   git clone https://github.com/czbiohub/special_ops_crispr_tools.git
   cd special_ops_cripr_tools
   make
   sudo make install
   ```
   **Note**: Use, e.g., `PREFIX=$HOME make install` to install `special_ops_crispr_tools` in a different location: you'll just need the `crispr_sites` and `offtarget` binaries in your path
2. Create and enter a Python virutal environment:
   ```bash
   python -m venv ~/.virtualenvs/dashit
   source ~/.virtualenvs/dashit/bin/activate
   ```
3. Install DASHit
   ```bash
   git clone https://github.com/czbiohub/guide_design_tools
   cd guide_design_tools
   make install
   ```

## Running DASHit
Once DASHit is installed, run it from the DASHit virtual environment.

```bash
source ~/.virtualenvs/dashit/bin/activate
dashit-reads-filter --help
crispr_sites -h
offtarget -h
optimize_guides -h
```

# Designing guides

1. Run `crispr_sites` to find all candidate guide RNA sequences in your input FASTQ
2. *Optional* Run `crispr_sites` to generate on-target and off-target files
3. Run `dashit-reads-filter` to remove candidate gRNAs that have poor structure (homopolymer, dinucleotide repeats, hairpins), represent adapter sequences, hit off targets, or don't hit on-targets
4. Run `optimize_guides` to find the gRNAs that hit the largest number of reads in your input FASTQ

To see how your designed guides perform, score your reads

# Scoring reads
