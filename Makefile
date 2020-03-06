PREFIX ?= /usr/local
SHELL := /bin/bash
DATA_DIR = /scratch
EXAMPLE_DASH_READS_DIR = ${DATA_DIR}/DASHit-reads
EXAMPLE_DASH_SEQ_DIR = ${DATA_DIR}/DASHit-seq
EXAMPLE_OUTPUT_DIR = ${DATA_DIR}/DASHit-example-output
VENDOR_DIR = vendor
SPECIAL_OPS_REPO = https://github.com/czbiohub/special_ops_crispr_tools.git
SPECIAL_OPS_DIR = special_ops_crispr_tools

SEQTK := $(shell command -v seqtk 2> /dev/null)

build-components: check-basic-deps get-vendor-deps build-special-ops-crispr-tools setup-dashit-filter build-score-guides optimize_guides

install-components: install-optimize-guides install-score-guides install-special-ops-crispr-tools

get-vendor-deps:
	rm -rf $(VENDOR_DIR)/$(SPECIAL_OPS_DIR)
	git clone $(SPECIAL_OPS_REPO) $(VENDOR_DIR)/$(SPECIAL_OPS_DIR)
	go get github.com/shenwei356/bio/seq
	go get github.com/shenwei356/bio/seqio/fastx
	go get github.com/shenwei356/xopen

build-score-guides:
	cd misc && go build -o score_guides

install-score-guides:
	install misc/score_guides $(PREFIX)/bin

build-special-ops-crispr-tools: get-vendor-deps
	cd $(VENDOR_DIR)/$(SPECIAL_OPS_DIR) && $(MAKE) 

install-special-ops-crispr-tools:
	cd $(VENDOR_DIR)/$(SPECIAL_OPS_DIR) && $(MAKE) install PREFIX=$(PREFIX)

check-basic-deps:
	bash check_basic_deps.sh || exit 1

install: 
	$(MAKE) install-components

optimize_guides: optimize_guides.go
	go build -o optimize_guides

setup-dashit-filter:
	pip3 install -r requirements.txt
	python3 setup.py develop

install-optimize-guides: optimize_guides
	install optimize_guides $(PREFIX)/bin

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
