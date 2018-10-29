# DASH analysis
DASHwrapper.sh illustrates a sample batch workflow for running score_guides to examine if a set of samples would undergo depletion by a given guide set or if a DASHed library contains any remaining material which should have been depleted. 

It performs subsampling, filtering, cutting TruSeq adaptors, converting to fasta, and running DASHit score_guides on a directory of fastq.gz files. Recommend to run in tmux/screen.

The wrapper also will format your standard output txt file from score_guides using a Python script. 

### Installation
Transfer or copy the DASHwrapper.sh and the Python scripts (DASH_csv_format_interactive.py and DASH_csv_format.py) into the directory with the files you wish to perform the analysis on.

### Dependencies
cutadapt 1.18 (script will upgrade your version)
PriceSeqFilter 1.2
seqtk
Python (script will install pandas)
DASHit

### Running the script

Use bash to run the script and follow with 3 arguments
1. the AWS path to your files
2. the path to the DASH guide library you want use to score your files
3. the prefix of your output file (outputfile)


```
bash DASHwrapper.sh s3://czbiohub-seqbot/fastqs/180907_A00111_0206_BH7W5WDSXX/rawdata/Amy_Lyden_AIH /mnt/data/specialops/DASH_Analysis/nribo2_150_V2.csv AIH_Plate_02_1xPCR_DASHed
```

### Your unformatted output file

Your unformatted CSV (outputfile_unformatted.csv) will contain three components.
1. score_guides output line
2. percent DASHed
3. a line with the total number of reads processed

### Your formatted output file
Your formatted CSV (outputfile.csv) will contain five columns
1. Guide library
2. Your filename
3. Total Reads DASHed (hit by scoreguides)
4. Total Reads in sample
5. Percent DASHed

### Running the Python script independently to format score_guides output
If you ran score_guides on a batch of files, and output to a txt file (outputfile.txt), you can run the Python scripts to reformat output_file.txt into a csv named outputfile.csv (see above for structure of formatted output file)

```
python DASH_csv_format.py outputfile
```

A version of the script will also parse your filename by underscores to create new columns and prompt you if you would like to keep this information column by column. This will create a file which is identical to the formatted output file, but has additional columns defined by you.
 
All of your filenames must have the same number of variables in the same order, and separated by underscores (ex: sample_treatmentgrp_date.fastq.gz). Use DASH_csv_format.py if this is not true.

Run the following command on outputfile.txt. Respond y/n depending on if you would like that column to be in your final file. If you respond y, you will be shown an example variable (ex: treatmentgrp) and prompted to enter a column name for the variable.

```
python DASH_csv_format_interactive.py outputfile
```
