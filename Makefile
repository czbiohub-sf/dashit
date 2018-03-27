DATA_DIR = /scratch/mcgeever
EXAMPLE_DASH_READS_DIR = ${DATA_DIR}/DASHit-reads
EXAMPLE_DASH_SEQ_DIR = ${DATA_DIR}/DASHit-seq
EXAMPLE_OUTPUT_DIR = ${DATA_DIR}/DASHit-example-output

setup: build-all install-all

build-all: build-optimize-guides build-score-guides build-cripsr-sites build-offtarget

build-optimize-guides:
	cd dashit && go build -o optimize_guides

build-score-guides:
	cd misc && go build -o score_guides

build-cripsr-sites:
	cd crispr_sites && $(MAKE)

build-offtarget:
	cd offtarget && go build -o offtarget

install-all: | install-ash install-dash-it install-deps

install-ash:
	cd ash && $(MAKE)

install-dash-it:
	cd dashit && $(MAKE)

install-deps:
	conda install -c bioconda seqtk -y

test:
	cd misc && go test -v

all-with-run: setup run-examples

run-examples: | run-examples-setup run-reads-example run-seq-example

run-examples-setup:
	mkdir -p $(EXAMPLE_OUTPUT_DIR)

run-reads-example:
	seqtk seq -A $(EXAMPLE_DASH_READS_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001.fastq > $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001.fasta
	cat $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001.fasta | crispr_sites/crispr_sites -r > $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_sites_to_reads.txt
	./dashit/optimize_guides $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_sites_to_reads.txt 100 1 > $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_guides.csv
	./misc/score_guides $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_guides.csv $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001.fasta -s
	mv NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_undashed.fasta $(EXAMPLE_OUTPUT_DIR)
	mv NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_dashed.fasta $(EXAMPLE_OUTPUT_DIR)
	./misc/score_guides $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_guides.csv $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_dashed.fasta
	./misc/score_guides $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_guides.csv $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_undashed.fasta

run-seq-example:
	$(MAKE) start-offtarget-server
	python dashit/dashit-seq/dashit-seq/dashit-seq.py $(EXAMPLE_DASH_SEQ_DIR)/rn45s-long.fa --offtarget $(EXAMPLE_DASH_SEQ_DIR)/mouse_transcriptome_sans_rn45s > $(EXAMPLE_OUTPUT_DIR)/mouse_rn45s_guides.csv
	$(MAKE) stop-offtarget-server

test-score-guides: | build-score-guides
	./misc/score_guides $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001_guides.csv $(EXAMPLE_OUTPUT_DIR)/NID0092_CSF_ATGTCAG-GGTAATC_L00C_R1_001.fasta -s

quick-test-score-guides: | build-score-guides
	./misc/score_guides misc/test_guides.csv misc/test_reads.fasta

start-offtarget-server:
	HOST=file:///$(EXAMPLE_DASH_SEQ_DIR)/mouse_transcriptome_sans_rn45s ./offtarget/offtarget &

stop-offtarget-server:
	- killall offtarget
