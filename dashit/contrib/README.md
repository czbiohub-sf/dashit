# DASH analysis
A wrapper script for subsampling, filtering, cutting TruSeq adaptors, converting to fasta, and running DASHit score guides on a directory of fastq.gz files. Recommend to run in tmux/screen so it can run independently.

### Installation
Transfer or copy the DASHwrapper.sh and the Python scripts (DASH_csv_format_interactive.py and DASH_csv_format.py) into the directory with the files you wish to perform the analysis on.

### Running the script

Use bash to run the script and follow with 3 arguments
1. the AWS path to your files
2. the path to the DASH guide library you want use to score your files
3. the prefix of your output file (outputfile)


```
bash DASHwrapper.sh s3://czbiohub-seqbot/fastqs/180907_A00111_0206_BH7W5WDSXX/rawdata/Amy_Lyden_AIH /mnt/data/specialops/DASH_Analysis/nribo2_150_V2.csv AIH_Plate_02_1xPCR_DASHed
```

### Your unformatted output file

Your unformatted CSV (outputfile_unformatted.csv) will contain five columns
1. Guide library
2. Your filename
3. Total Reads DASHed (hit by scoreguides)
4. Total Reads in sample
5. Percent DASHed

### Your formatted output file
After creating the unformatted CSV, the command line will parse your filename by underscores to create new columns and prompt you if you would like to keep this information column by column. Respond y/n depending on if you would like that column to be in your final file. This can be useful if you keep variables in your filename and would like to be able to sort and filter in Excel/R. 

However, all of your filenames must have the same number of variables in the same order, and separated by underscores. Use the unformatted version of the file if this is not true.

This file will be names outputfile.csv and will contain your DASH scoreguides output.
