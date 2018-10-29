
# coding: utf-8
# coding: utf-8

# In[2]: import pandas
import pandas as pd
import sys
import os

#take output file and read into dataframe
txtfile=sys.argv[1]
df=pd.read_csv("%s.txt" %txtfile,delimiter='\s',encoding='utf-8', engine ='python', header=None)


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
df.to_csv("%s_unformatted.csv" %txtfile)

# In[53]: split up the filename into variable based on underscore
variables = df['Filename'].str.split('_',expand=True)

# In[56]: loop over columns and ask user if they want to keep or name a column
colnames=[]
coltokeep=[]
for colnumber in variables.columns:
    exvar=variables.loc[0,colnumber]
    tokeep=input('What would you like to keep Column %s? An example variable is %s [y/n]' %(colnumber,exvar))
    if not tokeep=="n":
        colname=input('What would you like to name Column %s? ' %(colnumber))
        coltokeep.append(colnumber)
        colnames.append(colname)

# In[64]: create a dataframe with just the variables to keep
variablestoadd=pd.DataFrame(variables[coltokeep])

# In[66]: rename the variables kept with the column names input by user
variablestoadd.columns = colnames

# In[67]: add the variables to the main dataframe
df=pd.concat([df, variablestoadd],axis=1)

# In[23]: write to CSV file
df.to_csv("%s.csv" %txtfile)
