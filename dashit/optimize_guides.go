package main

import (
    "bufio"
	"io"
    "os"
    "fmt"
    "strings"
    "strconv"
	"math/rand"
	"sort"
	"github.com/shenwei356/bio/seqio/fastx"
)

func checkError(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func updateCounts(guidesToReads [][]int, coverage []int, counts []int, coverageNum int) {
    for guideIdx, guide := range guidesToReads {
        c := 0

        if counts[guideIdx] < 0 {
            // This guide has been used already, so don't update its count
            continue
        }
        
        for _, read := range guide {
			if coverage[read] < coverageNum {
                c++
            } 
        }

        counts[guideIdx] = c
    }
}

func coverReadsGreedy(guidesToReads [][]int, coverage []int, counts []int, maxGuides int, coverageNum int) []int {
    guides := make([]int, maxGuides)
    
    for i := 0; i < maxGuides; i++ {
        // Greedy: Find guide with largest count
        maxCount := -1
        maxCountIdx := -1
        
        for guideIdx, guideCount := range counts {
            if guideCount > maxCount {
                maxCount = guideCount
                maxCountIdx = guideIdx
            }
        }

        // take this guide!
        guides[i] = maxCountIdx
        for _, read := range guidesToReads[maxCountIdx] {
            coverage[read] += 1
        }

        // don't reuse the guide we just used
        counts[maxCountIdx] = -1
        
        updateCounts(guidesToReads, coverage, counts, coverageNum)

        if i % 20 == 0 {
            fmt.Fprintf(os.Stderr, "Found %d guides...\n", i + 1)
        }
    }

    return guides
}

func printUsage() {
    os.Stderr.WriteString("go run optimize_guides.go [input sites -> reads map] [number of crispr sites to return] [number of times to cover each read] [optional: reads file to output representative reads along with guides]\n")
}

func main() {
	if len(os.Args) < 4 {
        os.Stderr.WriteString("Error: Not enough input arguments\n")
        printUsage()
        os.Exit(-1);
    }

    inputFilename := os.Args[1]
    numSites, _ := strconv.Atoi(os.Args[2])
    coverageNum, _ := strconv.Atoi(os.Args[3])

	// optionally specify reads file
	var readsFile string = ""

	if len(os.Args) == 5 {
		readsFile = os.Args[4]
	}
	
    fmt.Fprintf(os.Stderr, "Choosing the %d sites from %s that will cover the most reads...\n", numSites, inputFilename)

    if file, err := os.Open(inputFilename); err == nil {
        defer file.Close()

        reader := bufio.NewReader(file)

        var guidesToReads [][]int

        var sites []string
        
        maxRead := 0

        maxNumReads := 0

        line, err := reader.ReadString('\n')
        
        for err == nil {
            readsStr := strings.Fields(line)

            sites = append(sites, readsStr[0])

            readsStr = readsStr[1:]

            reads := make([]int, 0)
			i := 0
			for _, rStr := range readsStr {
				r, _ := strconv.Atoi(rStr)

				readExists := false
				// A single guide can match a single read multiple
				// times, so check that we only add each read once
				for _, cur_r := range reads {
					if r == cur_r {
						readExists = true
						break
					}
				}

				if readExists == false {
					reads = append(reads, r)
					i = i + 1
					if r > maxRead {
						maxRead = r
					}
				}
            }

            if len(reads) > maxNumReads {
                maxNumReads = len(reads)
            }
            guidesToReads = append(guidesToReads, reads)

            line, err = reader.ReadString('\n')            
        }

        fmt.Fprintf(os.Stderr, "Largest # of reads hit by a single guide is %d\n", maxNumReads)

        coverage := make([]int, maxRead + 1)
        counts := make([]int, len(guidesToReads))

        updateCounts(guidesToReads, coverage, counts, coverageNum)

        guides := coverReadsGreedy(guidesToReads, coverage, counts, numSites, coverageNum)

		// build a cumulative sum of the number of reads covered as we
		// cumsum, we don't want to count reads that previous guides
		// have already hit

		readsCovered := make(map[int] bool)
		numReadsCovered := make([]int, numSites)

		for i, g := range guides {
			n := 0
			for _, r := range guidesToReads[g] {
				if readsCovered[r] == false {
					n += 1
					readsCovered[r] = true
				}
			}
			numReadsCovered[i] = n
		}
		
		readIdxToSeq := make(map[int] string)
		guideIdxToReadIdx := make([]int, numSites)
		
		if len(readsFile) > 0 {
			// collect a random read for each guide we've designed
			for i, g := range guides {
				guideIdxToReadIdx[i] = guidesToReads[g][rand.Intn(len(guidesToReads[g]))]
			}

			// Now we'll find the reads we chose in the specified
			// input FASTA file. Since this can be a big file, we'll
			// sort the read indices we need to lookup and find them
			// sequentially
			sortedReads := make([]int, len(guideIdxToReadIdx))
			copy(sortedReads, guideIdxToReadIdx)
			sort.Ints(sortedReads)

			nextReadIdx := 0
			
			reader, err := fastx.NewDefaultReader(readsFile)

			checkError(err)

			// Reads in normally formatted fasta files (that begin
			// with a >chromosome comment) are 1-indexed
			i := 1
				
			for {
				record, err := reader.Read()

				if err != nil {
					if err == io.EOF {
						break
					}
					checkError(err)
					break
				}

				if i == sortedReads[nextReadIdx] {
					nextReadIdx += 1
					readIdxToSeq[i] = fmt.Sprintf("%s", record.Seq.Seq)
					
					if nextReadIdx >= numSites {
						break
					}
				}

				i += 1
			}
			
			fmt.Printf("Site, Site index, Number of reads covered by site, cumulative number of reads covered, random read hit by this guide\n");
		} else {
			fmt.Printf("Site, Site index, Number of reads covered by site, cumulative number of reads covered\n");
		}

		cumulativeReadsCovered := 0
        for i, g := range guides {
            cumulativeReadsCovered += numReadsCovered[i]

			if len(readsFile) > 0 {
				fmt.Printf("%s, %d, %d, %d, %s\n", sites[g], g, numReadsCovered[i], cumulativeReadsCovered, readIdxToSeq[guideIdxToReadIdx[i]]);				
			} else {
				fmt.Printf("%s, %d, %d, %d\n", sites[g], g, numReadsCovered[i], cumulativeReadsCovered);				
			}
        }

        fmt.Fprintf(os.Stderr, "%d sites covered %d reads, # reads: %d\n", numSites, cumulativeReadsCovered, maxRead)
    }

    os.Stderr.Sync()
}

