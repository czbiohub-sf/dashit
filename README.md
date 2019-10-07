# DASHit: Guide design for DASH experiments

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

`DASHit` is a collection of software for the automated design and evaluation of Cas9 guide RNAs for DASH experiments ([1](#dash)).

1. <a name="dash"></a> Gu, W. et al. [Depletion of Abundant Sequences by Hybridization (DASH): using Cas9 to remove unwanted high-abundance species in sequencing libraries and molecular counting applications.](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-016-0904-5) Genome Biology 17, 41 (2016).

## Installation
`DASHit` runs on Linux and macOS. 
### Dependencies
Installing `DASHit` requires

1. A C++ compiler that supports C++11, e.g., a recent version of `g++` or `clang`
2. `go` version 1.9 or later
3. `python3`

On macOS, the quickest way to install these dependencies is via [homebrew](https://brew.sh/). Once homebrew is installed, you can run

```shell
brew install python
brew install go
# The xcode command line utilities will install clang
xcode-select --install
```
### DASHit
Then, to install DASHit:

```shell
git clone https://github.com/czbiohub/dashit
cd dashit
python3 -m venv ~/.virtualenvs/dashit
source ~/.virtualenvs/dashit/bin/activate
make install
```

By default this will install compiled binaries into
`/usr/local/bin`. To specify a different location for these compiled
binaries, set `PREFIX`, e.g.,

```shell
PREFIX=$HOME make install
```

**Note:** At least the `vendor/special_ops_crispr_tools/offtarget/offtarget` binary must be in your `PATH` in
order for `dashit_filter` to work.

## Documentation
Please visit [http://dashit.czbiohub.org](http://dashit.czbiohub.org) for documentation and examples.

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
Old versions of DASHit (pre 2.0), were licensed under the hybrid [Biohub License](./old-dashit-1.0.md), which was free for non-profit use, but required a separate
agreement for commercial use.
