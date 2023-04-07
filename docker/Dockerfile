FROM alpine:latest

# bash for scripts + to interact with the container
RUN apk add --no-cache bash

# c++ dependencies
RUN apk add --no-cache git g++ cmake make libgomp


# python dependencies
RUN apk add --no-cache python3 py3-pip
RUN pip3 install igraph
RUN apk --no-cache add py3-numpy
RUN apk --no-cache add py3-pandas
RUN pip3 install argh

# run package
RUN apk add --no-cache git
RUN git clone https://github.com/thobl/run run
WORKDIR /run
RUN pip3 install .

# R dependencies
ENV MAKE="make -j14"
RUN apk add --no-cache R R-dev linux-headers freetype-dev
RUN R -e 'install.packages(c("tidyverse"), repos="https://cloud.r-project.org/")'
RUN R -e 'install.packages(c("showtext"), repos="https://cloud.r-project.org/")'
RUN R -e 'install.packages(c("xtable", "plotly"), repos="https://cloud.r-project.org/")'
RUN R -e 'install.packages(c("patchwork"), repos="https://cloud.r-project.org/")'
RUN R -e 'install.packages(c("viridis"), repos="https://cloud.r-project.org/")'
RUN R -e 'install.packages(c("scales"), repos="https://cloud.r-project.org/")'
RUN R -e 'install.packages(c("latex2exp", "hexbin"), repos="https://cloud.r-project.org/")'

# Test dependencies
RUN R -e 'library(ggplot2)'
RUN R -e 'library(dplyr)'
RUN R -e 'library(latex2exp)'
RUN R -e 'library(viridis)'
RUN R -e 'library(tibble)'
RUN R -e 'library(tidyr)'
RUN R -e 'library(readr)'


## 
# Copy own code to repo
## 
ADD ./p_flattened_treewidth/code /cptw
# download public key for github.com
#ADD git@git.scc.kit.edu:scale/research/p_flattened_treewidth.git /cptw
#RUN git clone --recursive https://github.com/marcwil/cptw_code /cptw
#WORKDIR /cptw
#RUN git submodule init
#RUN git submodule update




# build girgs
WORKDIR /cptw/girgs
RUN chmod +x ./configure
RUN ./configure
RUN ./configure
RUN cmake --build ./build/
WORKDIR /cptw

# build findminhs
WORKDIR /cptw/findminhs
RUN apk add --no-cache cargo
RUN cargo build --release
WORKDIR /cptw

# build htd
WORKDIR /cptw/htd
run mkdir build
WORKDIR /cptw/htd/build
run cmake ..
run make
WORKDIR /cptw/



ENTRYPOINT tail -f /dev/null
