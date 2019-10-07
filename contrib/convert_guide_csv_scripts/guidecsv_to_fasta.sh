#! /bin/bash
# TITLE: guidecsv_to_fasta.sh
# DATE: April 20 2019
# AUTHOR: Amy Lyden
# USAGE: bash guidecsv_to_fasta.sh optimize_guides_output.csv

csv=$(echo $1 | cut -f 1 -d '.')
awk -F , -v csv=$csv '{print ">"csv"_"$1"\n"$2}' $1 | tail -n+5 > $csv.fasta
