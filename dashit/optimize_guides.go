package main

import (
    "bufio"
    "os"
    "fmt"
    "strings"
    "strconv"
)

func update_counts(guides_to_reads [][]int, coverage []bool, counts []int) {
    for guide_idx, guide := range guides_to_reads {
        c := 0

        for _, read := range guide {
			if coverage[read] == false {
                c++
            } 
        }

        counts[guide_idx] = c
    }
}

func cover_reads_greedy(guides_to_reads [][]int, coverage []bool, counts []int, max_guides int) ([]int, []int) {
    guides := make([]int, max_guides)
    readsCovered := make([]int, max_guides)
    
    for i := 0; i < max_guides; i++ {
        // Greedy: Find guide with largest count
        max_count := -1
        max_count_idx := -1
        
        for guide_idx, guide_count := range counts {
            if guide_count > max_count {
                max_count = guide_count
                max_count_idx = guide_idx
            }
        }

        // take this guide!
        guides[i] = max_count_idx
        readsCovered[i] = max_count
        for _, read := range guides_to_reads[max_count_idx] {
            coverage[read] = true
        }

        update_counts(guides_to_reads, coverage, counts)

        if i % 20 == 0 {
            fmt.Fprintf(os.Stderr, "Found %d guides...\n", i + 1)
        }
    }

    return guides, readsCovered
}

func printUsage() {
    os.Stderr.WriteString("go run optimize_guides.go [input sites -> reads map] [number of crispr sites to return]\n")
}

func main() {
    if len(os.Args) < 3 {
        os.Stderr.WriteString("Error: Not enough input arguments\n")
        printUsage()
        os.Exit(-1);
    }

    inputFilename := os.Args[1]
    numSites, _ := strconv.Atoi(os.Args[2])

    fmt.Fprintf(os.Stderr, "Choosing the %d sites from %s that will cover the most reads...\n", numSites, inputFilename)

    if file, err := os.Open(inputFilename); err == nil {
        defer file.Close()

        reader := bufio.NewReader(file)

        var guides_to_reads [][]int

        var sites []string
        
        max_read := 0

        max_num_reads := 0

        line, err := reader.ReadString('\n')
        
        for err == nil {
            reads_str := strings.Fields(line)

            sites = append(sites, reads_str[0])

            reads_str = reads_str[1:]

            reads := make([]int, len(reads_str))
            for i, r_str := range reads_str {
                r, _ := strconv.Atoi(r_str)
                reads[i] = r
                if r > max_read {
                    max_read = r
                }
            }

            if len(reads) > max_num_reads {
                max_num_reads = len(reads)
            }
            guides_to_reads = append(guides_to_reads, reads)

            line, err = reader.ReadString('\n')            
        }

        fmt.Fprintf(os.Stderr, "Largest # of reads hit by a single guide is %d\n", max_num_reads)

        coverage := make([]bool, max_read + 1)
        counts := make([]int, len(guides_to_reads))

        update_counts(guides_to_reads, coverage, counts)

        guides, readsCovered := cover_reads_greedy(guides_to_reads, coverage, counts, numSites)

        fmt.Printf("Site, Site index, Number of reads covered by site, cumulative number of reads covered\n");

		reads_covered := 0
        for i, g := range guides {
            reads_covered += readsCovered[i]
            fmt.Printf("%s, %d, %d, %d\n", sites[g], g, readsCovered[i], reads_covered);
        }

        fmt.Fprintf(os.Stderr, "%d sites covered %d reads, # reads: %d\n", numSites, reads_covered, max_read)
    }


    os.Stderr.Sync()
}
