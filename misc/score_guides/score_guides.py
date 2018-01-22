#!/usr/bin/env python3
import sys
import re

if __name__ == '__main__':
    sites_to_reads_filename = sys.argv[1]
    sites_filename = sys.argv[2]

    sites_to_reads = {}

    largest_read_idx = 0

    with open(sites_to_reads_filename, 'r') as sites_to_reads_file:
        lines = sites_to_reads_file.readlines()

        num_reads = None

        match = re.search(r'Total.+?(\d+)', lines[0])
        if match is not None:
            num_reads = int(match.group(1))
	    lines = lines[1:]

        for line in lines:
            line = line.split()
            sites_to_reads[line[0]] = [int(read) for read in line[1:]]
            if max(sites_to_reads[line[0]]) > largest_read_idx:
                largest_read_idx = max(sites_to_reads[line[0]])

    # If we didn't pickup the number of reads from the first line in
    # the file (e.g., processing an older file) use largest_read_idx
    # as the number of reads
    if num_reads is None:
        num_reads = largest_read_idx
        
    reads_covered = {}
    useless_guides = []
    
    with open(sites_filename, 'r') as sites_file:
        for line in sites_file.readlines()[2:]:
            site = line.split(',')[0].strip(' ')

            if site not in sites_to_reads:
                useless_guides.append(site)
                continue
            
            for read in sites_to_reads[site]:
                if read in reads_covered:
                    reads_covered[read] += 1
                else:
                    reads_covered[read] = 1

    print("{} will hit {}/{} = {:2.2g}% reads in {}, {} guides hit no reads".format(sites_filename, len(reads_covered.keys()), num_reads, len(reads_covered.keys())/float(num_reads) * 100, sites_to_reads_filename, len(useless_guides)))
