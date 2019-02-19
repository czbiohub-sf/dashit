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
echo $'\n##### Subsampling fastq.gz to 100k reads using seqtk #####\n'
for i in *.fastq.gz;
do seqtk sample -s100 $i 100000 > sub100k_${i:0:-3};
done;

#convert fastq to fasta
echo $'\n##### Converting fastq to fasta using seqtk #####\n'
for i in sub100k*; do seqtk seq -A $i > ${i:0:-4}asta; done;

#run score_guides
echo $'\n##### Running score_guides on all of your files using given guide library CSV #####\n'
for i in sub100k*.fasta; do score_guides $path_to_DASHguides $i >> ${output_file}.txt; done

#prepare to run python
echo $'\n##### Converting score_guides txt output to CSV file format using Python script DASH_csv_format.py #####\n'
pip install pandas -q
python DASH_csv_format.py $output_file.txt
