# guide_csv_to_fasta.sh

This script will convert an optimize guides csv output to a fasta file, numbering your guides and labelling them with your filename. If you input `optimize_guides_output.csv`, you will get `optimize_guides_output.fasta`.

```
bash guidecsv_to_fasta.sh optimize_guides_output.csv
```
# guide_csv_to_order.sh

This script will convert an optimize_guides csv output to a CSV file containing sequences to be ordered for synthesis. If you input `optimize_guides_output.csv`, you will get `optimize_guides_output_to_order.csv`.

The first row of the CSV will contain the header. The second row will contain the tracrRNA sequences. The following rows will include your crRNA sequences.

The CSV output will contain the following.
1. Guide name
2. Target sequence
3. Reverse complement of the target sequence
4. Guide RNA sequence (can order as RNA)
5. Guide RNA template with T7 transcription site (can order as DNA, along with T7 18mer `TAATACGACTCACTATAG`, and transcribe using T7 enzyme)

```
bash guidecsv_to_order.sh optimize_guides_output.csv
```
