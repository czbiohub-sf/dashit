Got junk sequences in your sequencing FASTQs? 

Many experiments are riddled with repetitive sequences which are of no
value to the scientific question you are asking. Some examples include
ribosomal RNA and hemoglobin. DASH ([1](#dash)) is a CRISPR-Cas9
next-generation sequencing (NGS) technology which depletes abundant
sequences, increasing coverage of your sequences of interest.

In the lab, you take final NGS libraries ready for sequencing, and
combine them with pre-programmed Cas9 guide RNAs (gRNAs) which cut up
your repetitive sequences into small fragments. You then size select
and amplify your remaining DNA, which should contain most or only your
sequences of interest. 

For more details on the wet lab side, [check out our actual protocol.](https://dx.doi.org/10.17504/protocols.io.6rjhd4n)

DASHit ([2](#dashit)) is the software that designs Cas9-gRNAs to target your particular experiment.


1. <a name="dash"></a> Gu, W. et al. [Depletion of Abundant Sequences by Hybridization (DASH): using Cas9 to remove unwanted high-abundance species in sequencing libraries and molecular counting applications.](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-016-0904-5) Genome Biology 17, 41 (2016).
2. <a name="dashit"></a> Dynerman, D. et al. `Preprint soon!`


# Installing 

Please visit the [GitHub repository](https://www.github.com/czbiohub/dashit) for instructions on how to install DASHit.

# Overview

`DASHit` is a collection of software to design Cas9 guide RNAs for a DASH experiment. The idea is to use an initial screening sequencing run to identify which sequences to target for depletion. `DASHit` analyzes this screening run to identify Cas9





# Scoring reads
