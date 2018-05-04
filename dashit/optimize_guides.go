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
    "regexp"
)

func checkError(err error) {
    if err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
}

// updateCounts updates how many reads each guide is currently
// hitting. Reads that have been covered by other guides are not
// counted. 
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

func coverReadsGreedy(guidesToReads [][]int, coverage []int, counts []int, maxGuides int, coverageNum int) ([]int, []int) {
    guides := make([]int, maxGuides)

    // How many new counts each chosen guide covers that weren't
    // covered by a previous guide
    countsChosen := make([]int, maxGuides)
    
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

	// for calculating statistics about how many reads our guide
	// set is covering, we only want to count reads for this guide
	// that haven't already been counted for another guide
	numUncoveredReads := 0    
	    
        // take this guide!
        guides[i] = maxCountIdx
        for _, read := range guidesToReads[maxCountIdx] {
	    if coverage[read] == 0 {
	        numUncoveredReads += 1
	    }
	    coverage[read] += 1
        }

        countsChosen[i] = numUncoveredReads
        
        // don't reuse the guide we just used
        counts[maxCountIdx] = -1
        
        updateCounts(guidesToReads, coverage, counts, coverageNum)

        if i % 20 == 0 {
            fmt.Fprintf(os.Stderr, "Found %d guides...\n", i + 1)
        }
    }

    fmt.Fprintf(os.Stderr, "Found %d guides...\n", len(guides))
    
    return guides, countsChosen
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
        
        maxNumReads := 0
       
        line, err := reader.ReadString('\n')

        var totalNumReadsRegExp = regexp.MustCompile(`Total.*?(\d+)`)

        if len(totalNumReadsRegExp.FindStringSubmatch(line)) == 0 {
            fmt.Fprintf(os.Stderr, "Error: Input file %s doesn't list total number of reads on the first line. Re-create this file with crispr_sites -r\n", inputFilename)
            os.Exit(-1)
        }
        
        var totalNumReads, _ = strconv.Atoi(totalNumReadsRegExp.FindStringSubmatch(line)[1])

        fmt.Fprintf(os.Stderr, "Total number of reads: %d\n", totalNumReads)
        
        line, err = reader.ReadString('\n')
        
        for err == nil {
            readsStr := strings.Fields(line)

            sites = append(sites, readsStr[0])

            readsStr = readsStr[1:]

            reads := make([]int, 0)
            for _, rStr := range readsStr {
                r, _ := strconv.Atoi(rStr)

                reads = append(reads, r)
            }

            if len(reads) > maxNumReads {
                maxNumReads = len(reads)
            }
            guidesToReads = append(guidesToReads, reads)

            line, err = reader.ReadString('\n')            
        }

        fmt.Fprintf(os.Stderr, "Largest # of reads hit by a single guide is %d\n", maxNumReads)

        coverage := make([]int, totalNumReads + 1)
        counts := make([]int, len(guidesToReads))

        updateCounts(guidesToReads, coverage, counts, coverageNum)

        guides, countsChosen := coverReadsGreedy(guidesToReads, coverage, counts, numSites, coverageNum)
        
        readIdxToSeq := make(map[int] string)
        guideIdxToReadIdx := make([]int, numSites)

        fmt.Printf("Total number of reads: %d\n", totalNumReads)
        
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
            cumulativeReadsCovered += countsChosen[i]

            if len(readsFile) > 0 {
                fmt.Printf("%s, %d, %d, %d, %s\n", sites[g], g, countsChosen[i], cumulativeReadsCovered, readIdxToSeq[guideIdxToReadIdx[i]]);                
            } else {
                fmt.Printf("%s, %d, %d, %d\n", sites[g], g, countsChosen[i], cumulativeReadsCovered);                
            }
        }

        fmt.Fprintf(os.Stderr, "%d sites covered %d reads, # reads: %d\n", numSites, cumulativeReadsCovered, totalNumReads)
    }

    os.Stderr.Sync()
}

