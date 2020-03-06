# DASHit: Guide design for DASH experiments
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

`DASHit` is a collection of software for the automated design and evaluation of Cas9 guide RNAs for DASH experiments ([1](#dash)).

1. <a name="dash"></a> Gu, W. et al. [Depletion of Abundant Sequences by Hybridization (DASH): using Cas9 to remove unwanted high-abundance species in sequencing libraries and molecular counting applications.](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-016-0904-5) Genome Biology 17, 41 (2016).

Made in SF with :hearts: and :microscope: by the [Biohub](https://www.czbiohub.org) Data Science Team.

## Documentation
Please visit [http://dashit.czbiohub.org](http://dashit.czbiohub.org) for documentation and examples.

## Running via Docker
The fastest way to get started with `DASHit` is to run our Docker image. Assuming the sequence files you want to process are in `/home/user/data`, simply run the `DASHit` image

```shell
docker run -it -v /Users/dynerman:/data czbiohub/dashit bash
```

Once you're in the container, navigate to the directory containing your sequence files and get started using `DASHit`!

```shell
cd /data
crispr_sites ...
```

See [http://dashit.czbiohub.org](http://dashit.czbiohub.org) for complete documentation and examples of guide design.

## Installation
If you're already running `DASHit` via Docker you're done! Visit [http://dashit.czbiohub.org](http://dashit.czbiohub.org) for examples showing how to run `DASHit`.

If you don't want to run `DASHit` with Docker, here are instructions for installing from source. `DASHit` runs on Linux and macOS. 

### Dependencies
Installing `DASHit` requires

1. A C++ compiler that supports C++11, e.g., a recent version of `g++` or `clang`
2. `go` version 1.9 or later
3. `python3`
4. *(Optional, but recommended)* [seqtk](https://github.com/lh3/seqtk) is a useful tool for manipulating FASTQ/A files. Once you compile `seqtk`, place it in your `PATH` (e.g., `install seqtk /usr/local/bin`)

On **macOS**, the quickest way to install `go` and `python3` is via [homebrew](https://brew.sh/). Once homebrew is installed, you can run

```shell
brew install python
brew install go
# The xcode command line utilities will install clang
xcode-select --install
```

On **Linux**, [download and install go here](https://golang.org/dl/), and then install `g++` and `python3` via your distributions package manager. On Ubuntu, this is

```shell
sudo apt-get update
sudo apt-get install build-essential
sudo apt-get install python3-pip
```
	

### DASHit
Then, to install DASHit:

```shell
git clone https://github.com/czbiohub/dashit
cd dashit
python3 -m venv ~/.virtualenvs/dashit
source ~/.virtualenvs/dashit/bin/activate
# Run the following two commands separately
make
sudo make install 
```

By default this will install compiled binaries into
`/usr/local/bin`. To specify a different location for these compiled
binaries, set `PREFIX`, e.g.,

```shell
PREFIX=$HOME make install
```

> **Note:** At least the `vendor/special_ops_crispr_tools/offtarget/offtarget` binary must be in your `PATH` in order for `dashit_filter` to work.

To test that everything installed correctly, open up a new shell, activate the virtualenv and take DASHit for a spin:

```shell
source ~/.virtualenvs/dashit/bin/activate
dashit_filter --help
crispr_sites -h
optimize_guides
echo "AAAAAAAAAAAAAAAAAAAA" > /tmp/mysequence.txt && HOST=file:///tmp/mysequence.txt offtarget
```

Press `CTRL+C` to exit `offtarget`.

## License
Copyright 2019 Chan-Zuckerberg Biohub

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

### Previous versions
Previous versions of DASHit were licensed under the hybrid [Biohub License](./old-dashit-1.0.md), which was free for non-profit use, but required a separate
agreement for commercial use.
