import json, csv, re, os, sys
import flash
from Bio import SeqIO
from collections import namedtuple
from colors import *

READ_LENGTH = 150
IDEAL_CUTOFF = 200
OKAY_CUTOFF = 301
LONG_CUTOFF = 501

Target = namedtuple('Target', ['guide', 'cut'])

class Component(object):
    """A collection of genes for which a single library will be built.
    The library can be subsetted to the guides cutting a certain
    set of genes."""
    def __init__(self, genes):
        self.genes = genes
        self.library = None
        self.name = genes[0].name + "-comp-" + str(len(self.genes))

    def set_library(self, library):
        self.library = library
        for g in self.genes:
            g.cut_with_library(library)

    def gene_names(self):
        return [g.name for g in self.genes]

    def subset_library(self, gene_subset, guide_subset=None):
        sub_library = set()
        if gene_subset != None:
            gene_subset = set(gene_subset)
        if guide_subset != None:
            guide_subset = set(guide_subset)
        for g in self.genes:
            if gene_subset == None or g.name in gene_subset:
                for target in g.cuts:
                    if guide_subset == None or target.guide in guide_subset:
                        sub_library.add(target.guide)

        assert sub_library <= set(self.library)

        return list(sub_library)

    def trim_library(self, n_cuts, gene_subset=None):
        # Trim the library to the extent possible,
        # keeping at least n_cuts segments per gene.
        # Returns the trimmed library.
        gene_names = set(g.name for g in self.genes)
        if gene_subset == None:
            gene_subset = set(gene_names)
        else:
            gene_subset = set(gene_subset) & gene_names
        guides = set()
        for gene in self.genes:
            if gene.name not in gene_subset or not gene.cuts:
                continue
            if gene.mutation_ranges:
                # we keep all cuts for genes with SNPs
                num_cuts = len(gene.cuts)
            else:
                num_cuts = min(n_cuts, len(gene.cuts))
            for cut in range(num_cuts):
                guides.add(gene.cuts[cut].guide)
        return list(guides)

        #raise NotImplementedError("TODO:  Trim library.")


class Gene(object):
    def __init__(self, name):

        self.name = name
        self.seq = None
        self.presence_absence = None
        self.aro = None
        self.mutation_ranges = None
        self.source = None

        self.padding = None
        self.resistance = None

        self.load_fasta()

        self.targets = None # List of (guide, cut location)

        # Product of cutting with a given library

        self.cuts = None # Location of each cut in sequence

        self.fragments = None # List of (start, end) for each fragment

    def load_fasta(self):
        try:
            f = open(os.path.join("generated_files/under_version_control/genes", self.name + ".fasta"))
            record = list(SeqIO.parse(f, "fasta"))[0]

            # Typical record id from CARD:
            #
            #     >gb
            #     |KF730651
            #     |+
            #     |0-657
            #     |ARO:3002796
            #     |QnrS7 [Escherichia coli]
            #     |flash_resistance:flash_todo
            #     |flash_key:QnrS7__KF730651__ARO_3002796
            #     |flash_padding:0_200
            #
            # (except all on one line)
            #
            s = str(record.description).split("|")
            for part in s:
                if part.startswith("ARO:"):
                    self.aro = int(part.split(':')[-1])
                if part.startswith("flash_padding:"):
                    prefix_str, suffix_str = part.split(':')[1].split('_')
                    self.padding = (int(prefix_str), int(suffix_str))
                if part.startswith("flash_resistance:"):
                    self.resistance = part.split(':')[1].split(',')
                if part.startswith("flash_mutation_ranges:"):
                    self.mutation_ranges = []
                    for rstr in part.split(':')[1].split(','):
                        rrng = MutationIndex.parse_mutation(rstr)
                        if type(rrng) == range:
                            self.mutation_ranges.append((rstr, rrng))
                        else:
                            print("ERROR: {}: Failed to parse mutation_range: {}".format(self.name, rstr))
            self.seq = record.seq
            if self.aro is not None:
                self.source = "CARD"
            else:
                self.source = "Resfinder"
        except FileNotFoundError:
            print(self.name, " is missing a fasta file.")

    def grants_resistance_to(self, antibiotic):
        if any(antibiotic in res for res in self.resistance):
            return True
        else:
            return False

    def load_targets(self, suffix):
        "Typical suffix is dna_good_5_9_18.txt"
        try:
            f = open(os.path.join("generated_files/under_version_control/gene_index", self.name, suffix), 'r')
            self.targets = []
            for line in f:
                (i, d) = line.strip().split()
                i = int(i)
                kmer = flash.forward_20mer_at(self.seq, i, d)
                self.targets.append(Target(kmer, flash.cut_location((i, d))))

        except FileNotFoundError:
            print(self.name, " is missing a target index file.")

    def verify_padding(self, padding_seq):
        assert padding_seq[0] in self.seq
        assert padding_seq[1] in self.seq
        assert self.padding == (len(padding_seq[0]), len(padding_seq[1]))

    def set_mutation_ranges(self):
        if self.mutation_ranges == None:
            self.mutation_ranges = []

    def get_mutation_ranges(self):
        if self.mutation_ranges is None:
            print("Mutation_ranges were never set.")
            return []

        if self.padding is None:
            return self.mutation_ranges
        else:
            padded_mutation_ranges = []
            for m, ran in self.mutation_ranges:
                # If we have added sequence of length p before the official start of the
                # gene as padding, then the location of the mutation in self.seq is p
                # after where it would be in the unpadded gene.
                #
                # TODO:  Move all this processing ot make_genes_and_identify_targets.py
                # and store the results in header metadata that can be loaded above.
                # That way more of the intermediate results can be reviewed and tracked.
                p = self.padding[0]
                padded_range = range(ran.start+p, ran.stop+p, ran.step)
                padded_mutation_ranges.append((m, padded_range))
            return padded_mutation_ranges

    def length(self):
        return len(self.seq)

    def has_snps(self):
        if len(self.mutation_ranges) > 0:
            return True
        else:
            return False

    def generate_fragments_from_cuts(self):
        self.fragments = [
            (self.cuts[i].cut, self.cuts[i+1].cut)for i in range(len(self.cuts) - 1)]

    def target_overlaps_mutation(self, target):
        if target.guide == self.seq[target.cut - 17 :target.cut + 3]:
            return self.range_overlaps_mutation(range(target.cut - 17,target.cut + 6))
        else:
            return self.range_overlaps_mutation(range(target.cut - 6, target.cut + 17))

    def range_overlaps_mutation(self, ran):
        for mutation, snp_range in self.get_mutation_ranges():
            for snp_loc in snp_range:
                if snp_loc in ran:
                    return True
        return False

    def cut_with_library(self, library):
        #The convention is: the fragments are given by seq[cut_1, cut_2].
        self.cuts = []
        for i in range(len(self.seq) - 23):
            kmer = self.seq[i:i+23]
            if kmer.endswith('GG'):
                target = str(kmer[:20])
                if target in library:
                    cutloc = i + 17
                    self.cuts.append(Target(target, cutloc))
                    if self.range_overlaps_mutation(range(i, i+23)):
                        print('Warning: guide %s overlaps with a mutation.' % target)
            if kmer.startswith('CC'):
                target = str(flash.reverse_complement(kmer)[:20])
                if target in library:
                    cutloc = i + 6
                    self.cuts.append(Target(target, cutloc))
                    if self.range_overlaps_mutation(range(i, i+23)):
                        print('Warning: guide %s overlaps with a mutation.' % target)

        self.cuts = sorted(self.cuts, key=lambda x: x.cut)
        self.generate_fragments_from_cuts()

    def coverage(self, min_fragment_size, max_fragment_size):
        covered_bases = 0
        for fragment in self.fragments:
            length = fragment[1] - fragment[0]
            if length >= min_fragment_size and length <= max_fragment_size:
                covered_bases += min(300, length)
        return covered_bases

    def possible_fragments(self):
        return (self.targets[-1].cut - self.targets[0].cut)//IDEAL_CUTOFF

    def longest_possible_fragment(self):
        return self.targets[-1].cut - self.targets[0].cut

    def stats(self):

        short_fragments = 0
        ideal_fragments = 0
        okay_fragments = 0
        long_fragments = 0

        for fragment in self.fragments:
            length = fragment[1] - fragment[0]
            if length < IDEAL_CUTOFF:
                short_fragments += 1
            elif length < OKAY_CUTOFF:
                ideal_fragments += 1
            elif length < LONG_CUTOFF:
                okay_fragments += 1
            else:
                long_fragments += 1
        ideal_and_okay_fragments = ideal_fragments + okay_fragments

        return {
                "gene_length": self.length(),
                "cuts": len(self.cuts),
                "ideal_fragments": ideal_fragments,
                "okay_fragments": okay_fragments,
                "ideal_and_okay_fragments": ideal_and_okay_fragments,
                "coverage": self.coverage(IDEAL_CUTOFF, LONG_CUTOFF),
                "possible_fragments": self.possible_fragments()
                }

    def display_gene_targets(self):

        arr = []
        for i in range(len(self.seq)):
            arr.append(["white", self.seq[i]])

        for mutation, snp_range in self.get_mutation_ranges():
            for i in snp_range:
                arr[i][0] = 'yellow'
                arr[i][1] = 'x'

        # Reverse order so that the indices of already-inserted cuts don't push the later indices to the wrong place.
        for target in self.targets[::-1]:
            if self.target_overlaps_mutation(target):
                arr.insert( target.cut, ['magenta', '|'])
            else :
                arr.insert(target.cut, ['cyan', '|'])

            #arr[target.cut][0] = 'cyan'
            #arr[target.cut][1] = arr[target.cut][1].tolower()

        for (i, (col, char)) in enumerate(arr):
            if i % 100 == 0:
                sys.stdout.write("\n")
            sys.stdout.write(color(char, bg=col))
        sys.stdout.flush()
        print()
        return 1

    def coverage(self):
        if self.cuts is None or self.fragments is None:
            print("Need to cut gene first.")
            return 0

        cov = 0
        for fragment in self.fragments:
            cov += min(2*READ_LENGTH, fragment[1] - fragment[0])

        return cov/len(self.seq)


    def display_gene_cuts(self):
        if self.cuts is None or self.fragments is None:
            print("Need to cut gene first.")
            return 0

        arr = []
        for i in range(len(self.seq)):
            arr.append(["white", self.seq[i]])

        for fragment in self.fragments:
            for i in range(fragment[0],
                           min(fragment[0]+READ_LENGTH, fragment[1])):
                arr[i][0] = 'green'
            for i in range(max(fragment[0], fragment[1]-READ_LENGTH),
                           fragment[1]):
                arr[i][0] = 'green'

        for mutation, snp_range in self.get_mutation_ranges():
            for i in snp_range:
                arr[i][0] = 'orange'
                arr[i][1] = 'x'

        # Reverse order so that the indices of already-inserted cuts don't push the later indices to the wrong place.
        for cut in self.cuts[::-1]:
            arr.insert(cut.cut, ['red', '|'])
            #arr[cut.cut][0] = 'red'
            #arr[cut.cut][1] = 'X'

        for (i, (col, char)) in enumerate(arr):
            if i % 100 == 0:
                sys.stdout.write("\n")
            sys.stdout.write(color(char, bg=col))
        sys.stdout.flush()
        print()
        return 1

class MutationIndex(object):
    def __init__(self, snp_file=None):
        if snp_file == None:
            snp_file = 'inputs/card/SNPs.txt'
        mutations = {}
        for row in csv.DictReader(open(snp_file), delimiter="\t"):
            if row['Accession'] and row['Mutations']:
                a = row['Accession']
                m = [s.strip() for s in row['Mutations'].split(',')]
                mutations[a] = mutations.get(a, []) + m
        self.mutations = mutations

    @staticmethod
    def parse_mutation(m):
        s = re.search("^[A-Z-](\d+)[A-Z-]$", m)
        if s:
            # eg: E502Q
            b = int(s.group(1))
            return range(b*3, b*3+3)
        else:
            # eg: nt420+2:GG
            s1 = re.search("^nt(\d+)\+(\d+)", m)
            if s1:
                x = int(s1.group(1))
                y = int(s1.group(2))
                return range(x, x+y)
            else:
                # eg: Y99STOP
                s2 = re.search("^[A-Z-](\d+)(STOP|fs)", m)
                if s2:
                    b = int(s2.group(1))
                    return range(b*3, b*3+2)
                else:
                    # eg: +nt349:CACTG
                    s3 = re.search("^\+nt(\d+):([A-Z-]+)$", m)
                    if s3:
                        b = int(s3.group(1))
                        return range(b, b+2)
                    else:
                        print("Mutation not parsed: ", m)
                        return None

    def mutation_ranges(self, aro):
        if str(aro) in self.mutations:
            ret = []
            for m in self.mutations[str(aro)]:
                    r = self.parse_mutation(m)
                    if r:
                        ret.append((m, r))
            return ret
        else:
            return []


def subset(components, gene_names, n_cuts=10):
    """
    Pull out only the cuts for gene_names from the given componenents.
    The result is a list of guides.
    """
    gene_names = set(gene_names)
    unsolved = set()
    results = []
    for c in components:
        c_subset = c.subset_library(gene_names, c.trim_library(n_cuts, gene_names))
        c_gene_names = set(c.gene_names())
        if not c_subset:
            unsolved |= (c_gene_names & gene_names)
        results.extend(c_subset)
    return results, unsolved
