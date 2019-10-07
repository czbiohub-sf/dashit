#! /bin/bash
# USAGE
# bash DASHwrapper.sh awspath path_to_DASHguides outputfile

aws_path=$1
path_to_DASHguides=$2
output_file=$3

#sync and unzip files
echo $'\n##### Downloading gunzipped files from AWS and removing Undetermined files if present #####\n'
aws s3 sync $aws_path . --exclude "*" --include "*.gz"
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
echo $'\n##### Converting score_guides txt output to CSV file format using Python script #####\n'
pip install pandas -q

python - $output_file.txt <<END
# In[2]: import pandas
import pandas as pd
import sys
import os

#take output file and read into dataframe
txtfile=sys.argv[1]
df=pd.read_csv("%s" %txtfile,delimiter='\s',encoding='utf-8', engine ='python', header=None)

# In[3]: create a list with rows to drop
rows=list(range(len(df)))
rows_to_drop=[2*x+1 for x in rows]
rows_to_drop= [x for x in rows_to_drop if x<(len(df)+1)]

# In[4]: drop all rows starting with total
df=df.drop(df.index[rows_to_drop])

# In[6]: reset the index to renumber everything
df=df.reset_index(drop=True)

# In[5]: select only the relevant columns from score_guides output
df = df[[3,5,7,9]]

# In[7]: rename columns


df=df.rename(index=int, columns={3 : "Guide Library", 5 : "Filename",7 : "Reads DASHed",9 : "Percent DASHed"})

# In[8]: parse out the name of the guide library file
guidelibrary = df['Guide Library'].str.split('/',expand=True)
df['Guide Library'] = guidelibrary[guidelibrary.columns[-1]]

# In[12]: get rid of percent sign in percent DASHed
df['Percent DASHed']=df['Percent DASHed'].str.strip('%')

# In[13]: parse out the total reads vs DASHed reads
reads = df['Reads DASHed'].str.split('/',expand=True)
reads= reads.rename(index=int, columns={ 0 : "total reads DASHed", 1 : "total reads"})
df=pd.concat([df, reads],axis=1)
df=df.drop('Reads DASHed',axis=1)

# In[23]: write to CSV file
outputfile= os.path.splitext(txtfile)[0]
df.to_csv("%s.csv" %outputfile)

END
