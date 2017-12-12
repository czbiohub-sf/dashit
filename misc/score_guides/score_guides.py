#!/usr/bin/env python3
import sys

if __name__ == '__main__':
    sites_to_reads_filename = sys.argv[1]
    sites_filename = sys.argv[2]

    sites_to_reads = {}

    largest_read_idx = 0
      
    with open(sites_to_reads_filename, 'r') as sites_to_reads_file:
        for line in sites_to_reads_file.readlines():
            line = line.split()
            sites_to_reads[line[0]] = [int(read) for read in line[1:]]
            if max(sites_to_reads[line[0]]) > largest_read_idx:
                largest_read_idx = max(sites_to_reads[line[0]])

    reads_covered = {}
    useless_guides = []
    
    with open(sites_filename, 'r') as sites_file:
        for line in sites_file.readlines()[1:]:
            site = line.split(',')[0].strip(' ')

            if site not in sites_to_reads:
                useless_guides.append(site)
                continue
            
            for read in sites_to_reads[site]:
                if read in reads_covered:
                    reads_covered[read] += 1
                else:
                    reads_covered[read] = 1


    total_reads_hit = sum([reads_covered[read] for read in reads_covered.keys()])
    print("{} will hit {}/{} = {:2.2g}% reads in {}, {} guides hit no reads".format(sites_filename, len(reads_covered.keys()), largest_read_idx, len(reads_covered.keys())/largest_read_idx * 100, sites_to_reads_filename, len(useless_guides)))
