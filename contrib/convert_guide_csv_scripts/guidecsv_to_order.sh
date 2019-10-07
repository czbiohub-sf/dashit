#! /bin/bash
# TITLE: guidecsv_to_order.sh
# AUTHOR: Amy Lyden
# USAGE: bash guidecsv_to_order.sh optimize_guides_output.csv

csv=$(echo $1 | cut -f 1 -d '.')
cut -f 2 -d ',' $1 | tr T U > gRNA.csv
cut -f 2 -d ',' $1 | rev | tr ATCG TAGC > revcomp_guide.csv
paste -d , revcomp_guide.csv gRNA.csv ${csv}.csv > revcomp_guide_full.csv
tail -n+3 revcomp_guide_full.csv > revcomp_guide.csv
printf "guide name,target sequence,rev comp target sequence,guide RNA,guide RNA template with T7 transcription site\ntracrRNA,NA,NA,GACAGCAUAGCAAGUUAAAAUAAGGCUAGUCCGUUAUCAACUUGAAAAAGUGGCACCGAGUCGGUGCUUUUU,AAAAAGCACCGACTCGGTGCCACTTTTTCAAGTTGATAACGGACTAGCCTTATTTTAACTTGCTATGCTGTCCTATAGTGAGTCGTATTA\n" > ${csv}_to_order.csv
awk -F , -v csv=$csv '{print csv"_crRNA_"$3","$4","$1","$2"GUUUUAGAGCUAUGCUGUUUUG,CAAAACAGCATAGCTCTAAAAC"$1"CTATAGTGAGTCGTATTA"}' revcomp_guide.csv >> ${csv}_to_order.csv
rm revcomp_guide_full.csv revcomp_guide.csv gRNA.csv
