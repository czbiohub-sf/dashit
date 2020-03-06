FROM ubuntu:18.04
LABEL maintainer="David Dynerman <david.dynerman@czbiohub.org>" license="Apache-2.0" url="http://dashit.czbiohub.org"
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update
RUN apt-get -y install apt-utils
RUN apt-get -y install build-essential python3-venv python3-pip git software-properties-common
RUN add-apt-repository -y ppa:longsleep/golang-backports
RUN apt-get -y update
RUN apt-get -y install golang-go
WORKDIR /
RUN git clone https://github.com/czbiohub/dashit
WORKDIR /dashit
RUN yes | make
RUN make install