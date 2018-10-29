#! /bin/bash
# USAGE
# bash DASHwrapper.sh awspath path_to_DASHguides outputfile

aws_path=$1
path_to_DASHguides=$2
output_file=$3

#sync and unzip files
echo $'\n##### Downloading files from AWS and removing Undetermined files if present #####\n'
aws s3 sync $aws_path .
rm Undetermined*

#subsample to 100,000 reads
echo $'\n##### Subsampling fastq.gz to 1 million reads #####\n'
for i in *.fastq.gz;
do seqtk sample -s100 $i 1000000 > sub1m_${i:0:-3};
done;

#filter files using PriceSeqFilter
echo $'\n##### Performing quality filtering using PriceSeqFilter #####\n'
for i in sub1m_*R1_001.fastq ; do PriceSeqFilter -a 20 -fp ${i:0:-11}1_001.fastq ${i:0:-11}2_001.fastq -op filt-85-98-90_${i:0:-11}1.fq filt-85-98-90_${i:0:-11}2.fq -pair both -rqf 85 0.98 -rnf 90; done;

#cut TruSeq adaptors
echo $'\n##### Performing adaptor trimming using cutadapt #####\n'
pip install --upgrade cutadapt
for i in filt*1.fq; do cutadapt --report=minimal -j 16 -a AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC -A AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT -o cut-${i:0:-4}1.fq -p cut-${i:0:-4}2.fq $i ${i:0:-4}2.fq -m 36; done;

#convert fastq to fasta
echo $'\n##### Converting fastq to fasta using seqtk #####\n'
for i in cut*; do seqtk seq -A $i > ${i:0:-1}asta; done;

#run score_guides
echo $'\n##### Running score_guides on all of your files using given guide library CSV #####\n'
for i in cut*.fasta; do score_guides $path_to_DASHguides $i >> ${output_file}.txt; done


tr "=" "," < $output_file.txt  > ${output_file}_unformatted.csv

#remove intermediate files
echo $'\n##### Removing intermediate subsampled, filtered and cut files #####\n'
rm sub1m*
rm filt*
rm cut*

#prepare to run python
echo $'\n##### Converting score_guides txt output to CSV file format using Python script DASH_csv_format.py #####\n'
pip install pandas
python DASH_csv_format.py $output_file
