#! /bin/bash
# TITLE: guidecsv_to_order.sh
# AUTHOR: Amy Lyden
# USAGE: bash guidecsv_to_order.sh optimize_guides_output.csv

csv=$(echo $1 | cut -f 1 -d '.')
tail -n+3 $1 > ${csv}_to_order.csv
cut -f 2 -d ',' $1 | grep '[ATCG]' | rev | tr ATCG TAGC > revcomp_guide.csv
paste -d , revcomp_guide.csv ${csv}_to_order.csv > revcomp_guide_full.csv
printf "guide name,target sequence,rev comp target sequence,guide RNA,guide RNA template with T7 transcription site\ntracrRNA,NA,NA,GACAGCATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGCTTTTT,AAAAAGCACCGACTCGGTGCCACTTTTTCAAGTTGATAACGGACTAGCCTTATTTTAACTTGCTATGCTGTCCTATAGTGAGTCGTATTA\n" > ${csv}_to_order.csv
awk -F , -v csv=$csv '{print csv"_crRNA_"$2","$3","$1","$3"GTTTTAGAGCTATGCTGTTTTG,CAAAACAGCATAGCTCTAAAAC"$1"CTATAGTGAGTCGTATTA"}' revcomp_guide_full.csv >> ${csv}_to_order.csv
rm revcomp_guide_full.csv revcomp_guide.csv
