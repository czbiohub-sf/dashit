#! /bin/bash
# USAGE
# bash DASHwrapper.sh awspath path_to_DASHguides outputfile

aws_path=$1
path_to_DASHguides=$2
output_file=$3

#sync and unzip files
aws s3 sync $aws_path .
rm Undetermined*

#subsample to 100,000 reads
for i in *.fastq.gz;
do seqtk sample -s100 $i 1000000 > sub1m_${i:0:-3};
done;

#filter files using PriceSeqFilter
for i in sub1m_*R1_001.fastq ; do PriceSeqFilter -a 20 -fp ${i:0:-11}1_001.fastq ${i:0:-11}2_001.fastq -op filt-85-98-90_${i:0:-11}1.fq filt-85-98-90_${i:0:-11}2.fq -pair both -rqf 85 0.98 -rnf 90; done;

#cut TruSeq adaptors
pip install cutadapt
for i in filt*1.fq; do cutadapt -j 16 -a AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC -A AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT -o cut-${i:0:-4}1.fq -p cut-${i:0:-4}2.fq $i ${i:0:-4}2.fq -m 36; done;

#convert fastq to fasta
for i in cut*; do seqtk seq -A $i > ${i:0:-1}asta; done;

#run score_guides
for i in cut*.fasta; do score_guides $path_to_DASHguides $i >> ${output_file}.txt; done

tr "=" "," < $output_file.txt  > ${output_file}_unformatted.csv

#remove intermediate files
rm filt*.fq
rm filt*fasta

#prepare to run python
pip install pandas
python DASH_csv_format.py $output_file
