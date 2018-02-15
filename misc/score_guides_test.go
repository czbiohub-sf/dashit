package main

import (
	"fmt"
	"github.com/shenwei356/bio/seqio/fastx"
	"io/ioutil"
	"os"
	"os/exec"
	"reflect"
	"testing"
)

const ExpectedDashedFileName = "tests/data/test_expected_reads_dashed.fasta"
const ExpectedUnDashedFileName = "tests/data/test_expected_reads_undashed.fasta"
const ProducedDashedFileName = "test_reads_dashed.fasta"
const ProducedUnDashedFileName = "test_reads_undashed.fasta"
const TestReadsFileName = "tests/data/test_reads.fasta"
const TestGuidesFileName = "tests/data/test_guides.csv"

func cleanUp() {
	err := os.RemoveAll(ProducedDashedFileName)
	if err != nil {
		fmt.Printf("Unable to remove: %s\n", ProducedDashedFileName)
		os.Exit(1)
	}

	err = os.RemoveAll(ProducedUnDashedFileName)
	if err != nil {
		fmt.Printf("Unable to remove: %s\n", ProducedUnDashedFileName)
		os.Exit(1)
	}
}


func TestMain(m *testing.M) {
	cleanUp()
	m.Run()
	cleanUp()
}

func TestSetHitsAndMisses(t *testing.T) {
	expectedHits := 2
	expectedTotal := 5

	reader, err := fastx.NewDefaultReader(TestReadsFileName)
	if err != nil {
		t.Errorf("Could not read %s\n", TestReadsFileName)
	}

	guides := getGuides(TestGuidesFileName)

	readHits := &NoSplitReadHits{}

	SetHitsAndMisses(reader, guides, readHits)

	if readHits.getHits() != expectedHits {
		t.Error("Expected %v hits got: %v", expectedHits, readHits.getHits())
	}

	if readHits.getTotal() != expectedTotal {
		t.Error("Expected %v reads total got: %v", expectedTotal, readHits.getTotal())
	}
}

func TestMainFunction(t *testing.T) {
	cmd := exec.Command("./score_guides", TestGuidesFileName, TestReadsFileName, "-s")
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Errorf("Error: %s %s", out, err)
	}

	verifyFilesAreTheSame(ProducedDashedFileName, ExpectedDashedFileName, t)
	verifyFilesAreTheSame(ProducedUnDashedFileName, ExpectedUnDashedFileName, t)
}

func verifyFilesAreTheSame(fileName1, fileName2 string, t *testing.T) {
	file1Content, err := ioutil.ReadFile(fileName1)
	if err != nil {
		t.Errorf("Failed to read file %s for comparison check.\n")
	}

	file2Content, err := ioutil.ReadFile(fileName2)
	if err != nil {
		t.Errorf("Failed to read file %s for comparison check.\n")
	}

	if !reflect.DeepEqual(file1Content, file2Content) {
		t.Errorf(
			"Contents of %s do not equal the contents of file %s\n",
			fileName1,
			fileName2,
		)
	}

}
