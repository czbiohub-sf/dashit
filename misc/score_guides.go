package main

import (
	"fmt"
	"io"
	"os"
    "strings"
    "bufio"
    "time"
	"github.com/shenwei356/bio/seq"
	"github.com/shenwei356/bio/seqio/fastx"
    "bytes"
	"github.com/shenwei356/xopen"
    "path"
)

func printUsage() {
    fmt.Fprintf(os.Stderr, "Usage:\n\tscore_guides guides.csv reads.fasta [-s]\n")
    fmt.Fprintf(os.Stderr, "\n\tScore guides against a FASTA file\n")
    fmt.Fprintf(os.Stderr, "\n\t\tguides.csv\tCRISPR guides, as produced by optimize_guides\n")
    fmt.Fprintf(os.Stderr, "\t\treads.fasta\tFASTA file to measure guide hits against\n")
    fmt.Fprintf(os.Stderr, "\n\tOptional Flags\n")
    fmt.Fprintf(os.Stderr, "\n\t\t-s\tSplit DASHed and unDASHed reads from reads.fasta\n")
}

func main() {
    if len(os.Args) < 3 {
        printUsage()
        os.Exit(-1)
    }

    splitFasta := false

    guidesFilename := os.Args[1]
    fastaFilename := os.Args[2]

    if len(os.Args) > 3 {
        if os.Args[3][0] == '-' {
            if os.Args[3][1] == 's' {
                splitFasta = true
            } else {
                fmt.Fprintf(os.Stderr, "Error: Unrecognized flag %s\n", os.Args[1])
                printUsage()
                os.Exit(-1)
            }
        }
    }
    
    guidesFile, err := os.Open(guidesFilename)
    checkError(err)
    defer guidesFile.Close()

    scanner := bufio.NewScanner(guidesFile)

    // Skip metadata on first two lines of the guides file
    scanner.Scan()
    scanner.Scan()
    
    guides := make([]*seq.Seq, 0, 50)
    
    for scanner.Scan() {
        newSeq, err := seq.NewSeq(seq.DNA, []byte(strings.Split(scanner.Text(), ",")[0]))
        checkError(err)
        guides = append(guides, newSeq)

        if guides[len(guides) - 1].Length() != 20 {
            fmt.Fprintf(os.Stderr, "Expected a 20-mer guide in %s, got %s\n", os.Args[1], guides[len(guides) - 1])
            os.Exit(-1)
        }
    }

	// // use buffered out stream for output
	// outfh, err := xopen.Wopen("-") // "-" for STDOUT
	// checkError(err)
	// defer outfh.Close()

	// // disable sequence validation could reduce time when reading large sequences
	// // seq.ValidateSeq = false

    fmt.Fprintf(os.Stderr, "Scoring guides against %s\n", fastaFilename)
    ioStart := time.Now()
    
	reader, err := fastx.NewDefaultReader(fastaFilename)
    checkError(err)
    hits := 0
    total := 0

    var dashedFile, undashedFile *xopen.Writer
    var dashedFilename, undashedFilename string
    
    if splitFasta {
        basename := path.Base(fastaFilename)
        basename = strings.TrimSuffix(basename, path.Ext(basename))

        dashedFilename = basename + "_dashed.fasta"
        undashedFilename = basename + "_undashed.fasta"
        
        dashedFile, err = xopen.Wopen(dashedFilename)
        checkError(err)
        defer dashedFile.Close()
        
        undashedFile, err = xopen.Wopen(undashedFilename)
        checkError(err)
        defer undashedFile.Close()
    }

    var readHit bool

    
    for {
        record, err := reader.Read()
        if err != nil {
            if err == io.EOF {
                break
            }
            checkError(err)
            break
        }

        readHit = false
        
        for _, g := range guides {
            if bytes.Contains(record.Seq.Seq, g.Seq) {
                readHit = true
                break
            }
        }

        if readHit {
            hits = hits + 1
            
            if splitFasta {
                record.FormatToWriter(dashedFile, 0)
            }
        } else if splitFasta {
            record.FormatToWriter(undashedFile, 0)
        }

        total = total + 1
    }

    fmt.Fprintf(os.Stdout, "%d guides in %s vs. %s hit %d/%d = %.2f%%\n", len(guides), guidesFilename, fastaFilename, hits, total, 100.0 * float32(hits) / float32(total))

    fmt.Fprintf(os.Stderr, "Parsing FASTA took %s\n", time.Since(ioStart))

    if splitFasta {
        fmt.Fprintf(os.Stderr, "Wrote %s\n", dashedFilename)
        fmt.Fprintf(os.Stderr, "Wrote %s\n", undashedFilename)        
    }
}

func checkError(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
