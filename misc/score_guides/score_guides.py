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
            site = line.split()[0][:-1]

            if site not in sites_to_reads:
                useless_guides.append(site)
                continue
            
            for read in sites_to_reads[site]:
                if read in reads_covered:
                    reads_covered[read] += 1
                else:
                    reads_covered[read] = 1
          
    print("These guides will hit {}/{} = {:2.2g}% reads, {} guides hit no reads".format(len(reads_covered.keys()), largest_read_idx, len(reads_covered.keys())/largest_read_idx * 100, len(useless_guides)))
