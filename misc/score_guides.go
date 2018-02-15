package main

import (
	"bufio"
	"bytes"
	"fmt"
	"github.com/shenwei356/bio/seq"
	"github.com/shenwei356/bio/seqio/fastx"
	"github.com/shenwei356/xopen"
	"io"
	"os"
	"path"
	"strings"
	"time"
)

type ReadHitable interface {
	recordHit(record *fastx.Record)
	recordMiss(record *fastx.Record)
	getHits() int
	getTotal() int
}

type ReadHits struct {
	hits, misses int
}

func (rh *ReadHits) recordHit(record *fastx.Record) {
	rh.hits++
}

func (rh *ReadHits) recordMiss(record *fastx.Record) {
	rh.misses++
}

func (rh *ReadHits) getHits() int {
	return rh.hits
}

func (rh *ReadHits) getTotal() int {
	return rh.hits + rh.misses
}

type NoSplitReadHits struct {
	ReadHits
}

type SplitReadHits struct {
	ReadHits
	dashedFile, undashedFile *xopen.Writer
}

func (srh *SplitReadHits) recordHit(record *fastx.Record) {
	srh.ReadHits.recordHit(record)
	// TODO(AM): Make sure to handle errors with writing here.
	record.FormatToWriter(srh.dashedFile, 0)
}

func (srh *SplitReadHits) recordMiss(record *fastx.Record) {
	srh.ReadHits.recordMiss(record)
	// TODO(AM): Make sure to handle errors with writing here.
	record.FormatToWriter(srh.undashedFile, 0)
}

func printUsage() {
	fmt.Fprintf(os.Stderr, "Usage:\n\tscore_guides guides.csv reads.fasta [-s]\n")
	fmt.Fprintf(os.Stderr, "\n\tScore guides against a FASTA file\n")
	fmt.Fprintf(os.Stderr, "\n\t\tguides.csv\tCRISPR guides, as produced by optimize_guides\n")
	fmt.Fprintf(os.Stderr, "\t\treads.fasta\tFASTA file to measure guide hits against\n")
	fmt.Fprintf(os.Stderr, "\n\tOptional Flags\n")
	fmt.Fprintf(os.Stderr, "\n\t\t-s\tSplit DASHed and unDASHed reads from reads.fasta\n")
}

func SetHitsAndMisses(reader *fastx.Reader, guides []*seq.Seq, rh ReadHitable) {
	var foundReadHit bool

	for {
		record, err := reader.Read()
		if err != nil {
			if err == io.EOF {
				break
			}
			checkError(err)
			break
		}

		foundReadHit = false

		for _, g := range guides {
			if bytes.Contains(record.Seq.Seq, g.Seq) {
				foundReadHit = true
				break
			}
		}

		if foundReadHit {
			rh.recordHit(record)
		} else {
			rh.recordMiss(record)
		}
	}
}

func getGuides(guidesFilename string) []*seq.Seq {
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

		if guides[len(guides)-1].Length() != 20 {
			fmt.Fprintf(os.Stderr, "Expected a 20-mer guide in %s, got %s\n", os.Args[1], guides[len(guides)-1])
			os.Exit(-1)
		}
	}

	return guides
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

	guides := getGuides(guidesFilename)

	fmt.Fprintf(os.Stderr, "Scoring guides against %s\n", fastaFilename)
	ioStart := time.Now()

	reader, err := fastx.NewDefaultReader(fastaFilename)
	checkError(err)

	var dashedFile, undashedFile *xopen.Writer
	var dashedFilename, undashedFilename string

	var readHits ReadHitable

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

		readHits = &SplitReadHits{dashedFile: dashedFile, undashedFile: undashedFile}
	} else {
		readHits = &NoSplitReadHits{}
	}

	SetHitsAndMisses(reader, guides, readHits)

	fmt.Fprintf(
		os.Stdout,
		"%d guides in %s vs. %s hit %d/%d = %.2f%%\n",
		len(guides),
		guidesFilename,
		fastaFilename,
		readHits.getHits(),
		readHits.getTotal(),
		100.0*float32(readHits.getHits())/float32(readHits.getTotal()),
	)

	fmt.Fprintf(os.Stderr, "Parsing FASTA took %s\n", time.Since(ioStart))

	if splitFasta {
		fmt.Fprintf(os.Stderr, "Wrote %s\n", dashedFilename)
		fmt.Fprintf(os.Stderr, "Wrote %s\n", undashedFilename)
	}

	fmt.Println("Total is:", readHits.getTotal())
}

func checkError(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
