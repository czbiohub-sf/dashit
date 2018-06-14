SHELL := /bin/bash
DATA_DIR = /scratch
EXAMPLE_DASH_READS_DIR = ${DATA_DIR}/DASHit-reads
EXAMPLE_DASH_SEQ_DIR = ${DATA_DIR}/DASHit-seq
EXAMPLE_OUTPUT_DIR = ${DATA_DIR}/DASHit-example-output
VENDOR_DIR = vendor
SPECIAL_OPS_REPO = git@github.com:czbiohub/special_ops_crispr_tools.git
SPECIAL_OPS_DIR = special_ops_crispr_tools

SEQTK := $(shell command -v seqtk 2> /dev/null)

get-vendor-deps:
	rm -rf $(VENDOR_DIR)/$(SPECIAL_OPS_DIR)
	git clone $(SPECIAL_OPS_REPO) $(VENDOR_DIR)/$(SPECIAL_OPS_DIR)

build-components: build-optimize-guides build-score-guides build-special-ops-crispr-tools

build-optimize-guides:
	cd dashit && go build -o optimize_guides

build-score-guides:
	cd misc && go build -o score_guides

build-special-ops-crispr-tools:
	cd $(VENDOR_DIR)/$(SPECIAL_OPS_DIR) && $(MAKE)

check-basic-deps:
	bash check_basic_deps.sh || exit 1

check-license-agreement:
	bash check_license.sh || exit 1

install: check-license-agreement check-basic-deps
	$(MAKE) install-components

install-components: get-vendor-deps build-components install-dashit

install-dashit:
	cd dashit && $(MAKE)

test:
	cd misc && go test -v

all-with-run: install run-examples

run-examples: | run-examples-setup run-reads-example run-seq-example

run-examples-setup:
	mkdir -p $(EXAMPLE_OUTPUT_DIR)

run-reads-example:
	ifndef SEQTK
	    $(error "running the examples requires seqtk to be installed and in your path")
	endif

	seqtk seq -A $(EXAMPLE_DASH_READS_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001.fastq > $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001.fasta
	cat $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001.fasta | $(VENDOR_DIR)/$(SPECIAL_OPS_DIR)/crispr_sites/crispr_sites -r > $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_sites_to_reads.txt
	./dashit/optimize_guides $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_sites_to_reads.txt 100 1 > $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_guides.csv
	./misc/score_guides $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_guides.csv $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001.fasta -s
	mv NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_undashed.fasta $(EXAMPLE_OUTPUT_DIR)
	mv NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_dashed.fasta $(EXAMPLE_OUTPUT_DIR)
	./misc/score_guides $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_guides.csv $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_dashed.fasta
	./misc/score_guides $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_guides.csv $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_undashed.fasta

run-seq-example:
	PATH=$$PATH:$(VENDOR_DIR)/$(SPECIAL_OPS_DIR)/offtarget \
	python dashit/dashit-seq/dashit-seq/dashit-seq.py $(EXAMPLE_DASH_SEQ_DIR)/rn45s-long.fa --offtarget $(EXAMPLE_DASH_SEQ_DIR)/mouse_transcriptome_sans_rn45s > $(EXAMPLE_OUTPUT_DIR)/mouse_rn45s_guides.csv

test-score-guides: | build-score-guides
	./misc/score_guides $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_guides.csv $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001.fasta -s

quick-test-score-guides: | build-score-guides
	./misc/score_guides misc/test_guides.csv misc/test_reads.fasta
