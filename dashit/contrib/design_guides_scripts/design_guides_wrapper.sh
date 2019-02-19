#! /bin/bash
# USAGE
# bash design_guides_wrapper.sh reads_prefix on_target_fasta off_target_fasta

reads_prefix=$1
on_target=$2
off_target=$3

echo $'\n##### Running crispr_sites -r on your reads #####\n'
cat $reads_prefix* | crispr_sites -r > reads_crispr_sites.txt

echo $'\n##### Running crispr_sites on your on-target and off-target fastas  #####\n'
cat $on_target | crispr_sites > on_target_crispr_sites.txt
cat $off_target | crispr_sites > off_target_crispr_sites.txt

echo $'\n##### Running dashit_reads_filter.py to extract on-target crispr sites in your reads  #####\n'
python3 ../../dashit-reads/dashit_reads/dashit_reads_filter.py reads_crispr_sites.txt --offtarget off_target_crispr_sites.txt --offtarget_radius 5_10_20 --ontarget on_target_crispr_sites.txt --ontarget_radius 5_10_20 --filtered_explanation why_final_guides.csv > final_crispr_sites.txt
#remove first two lines of file
sed -i 1,2d final_crispr_sites.txt

let number_of_guides=$(cat final_crispr_sites.txt | wc -l)-1

echo $'\n##### The number of final guides that are on-target and in your reads is ' $number_of_guides $' #####\n'

echo $'\n##### Running optimize_guides to determine number of reads hit per guide  #####\n'

optimize_guides final_crispr_sites.txt $number_of_guides 1 > final_guides.csv

echo $'\n##### Running score_guides to determine what percentage of reads are targeted by full guide set  #####\n'
for i in $reads_prefix*; do score_guides final_guides.csv $i >> final_guides_scored.txt; done

echo $'\n##### Converting score_guides txt output to CSV file format using Python script DASH_csv_format.py #####\n'
pip install pandas -q

python - <<END
# In[2]: import pandas
import pandas as pd
import sys
import os

#take output file and read into dataframe
df=pd.read_csv('final_guides_scored.txt',delimiter='\s',encoding='utf-8', engine ='python', header=None)


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
df.to_csv("final_guides_scored_formatted.csv")

END
