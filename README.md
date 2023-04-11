# CPTW Code

Code and plotting scripts for the paper

> Thomas Bläsius, Maximilian Katzmann and Marcus Wilhelm: Partitioning the Bags of a Tree Decomposition Into Cliques.
> https://arxiv.org/abs/2302.08870

This repository contains all code and evaluation scripts to reproduce our experiments. Below, we explain how to run our experiments using Docker (most convenient) or locally.

## Running with pre-build docker image

**Running the container**

Use the following commands to download Docker image.

    wget https://zenodo.org/record/7816985/files/cptw.zip
    unzip cptw.zip

Afterwards, load the image and run it…

    cd cptw
    ./load.sh
    ./run.sh

… and enter the container:

    ./enter.sh
  
If you are running on a server and might want to log out while the experiments are running, consider running the last command in a `tmux` or `screen` session.

**Running the experiments**

Inside the container, we first have to download a dataset of networks and some fonts, by executing the following command.

    ./prepare.sh
    
Next, we run the experiments (this might take some time).

    ./run_all_experiments.sh
    
The results from the experiments are written to `.csv` files in `./output_data`.
We use

    ./generate_plots.sh

to run R script generating the plots used in the paper as well as some additional plots.

Afterwards, we log out and stop the container:

    exit
    ./kill.sh

The results should now be in `./data/`.

## Running experiments natively

### Preparation

- Clone repository recursively
- Build `girgs`, `findminhs`, and `htd` submodules according to instructions in
  submodules
- Download networks using `./prepare.sh`
- Install Python dependencies:
  - Run: `https://github.com/thobl/run`
  - `igraph`
  - `numpy`
  - `pandas`
  - `argh`
  - `pytest` (for testing)

### Running experiments

Experiments are defined in `run_experiments.py` and experiment results are
written to `./output_data`. If results are already present in `./output_data`,
the corresponding experiments are skipped. The script `clear_output.sh` can be
used to remove the results already present in this repository.


To run all experiments, execute `./run_all_experiments.sh`.

To run a specific experiment (e.g. `girg_scaling`) execute `python
run_experiments.py girg_scaling` and then `python run_experiments.py post`.

### Plotting

Plotting scripts are under `plotting`, can be called using `Rscript
<script_name.R>` and write the resulting PDFs into the directory `./output.pdf`.

To run all plotting scripts, execute `./generate_plots.sh`.

## Explanation / Experiment Setup

The experiments are run using a [run](https://github.com/thobl/run) configuration
specified in `run_experiments.py`. Calling `python run_experiments.py` shows a
list of all defined experiments, structured into groups `exp_rw`, `girg`, etc.
The experiments in `exp_rw` are running on the real-world networks downloaded into
`./input_data/` using `./prepare.sh`. Individual experiments can be run using
`python run_experiments.py exp_rw` or `python run_experiments.py girg_flc`.

The output of an experiment `name` is written to `./output_data/name/`. For plotting,
it is necessary, to merge all `.csv`-files in `./output_data/name/` to
`./output_data/name.csv`, using `python run_experiments merge_name` or to merge the 
files of all experiments `python run_experiments post`. 

Typically, the output of an experiment consists of many `.csv`-files (e.g. one per
real world network or one per girg parameter set) and if an experiment is aborted
(e.g. by pressing `CTRL+c`) already written outputs will be kept. When re-running an
experiment the previous progress will be recovered.

The plots are generated using the `R` script in `./plotting/`. The file `./plotting/helper.R`
commonly used settings and imports and `./plotting/data_helper.R` contains functions
for reading the `.csv`-files created by the experiments. Individual plots are grouped into
semantically named files like `./plotting/network_properties.R` or `./plotting/scaling_plots.R`.

Most experiments rely on the python modules under `./pftpy/`. A general framework for
the flexible definition of algorithmic experiments in contained in `./pftpy/actions` and
specific steps of our algorithm are contained in `./pftpy/graph_actions`. In particular,
the branch-and-bound solver is implemented in `./pftpy/graph_actions/partition.py`.
The framework allows to specify runs of the with varying flexible components,
such as different inputs or different partitioning algorithms. For usage examples consider
the following calls or browse through `run_experiments.py`.

    python pftpy/algo.py run -f "GraphInput:girg" "GirgGen(n=500,d=1,deg=10,seed=50771,ple=2.3,alpha=5.375)" \
    "Algo:part_treedec" "HTD(seed=42,variant=minfill,timeout=300)" "Partition:branch" \
    "PartitionBags(timeout=10)" "BranchingPartition(timeout=10)" "Output(printer=json)"

Here, the branch and bound solver is run on a girg and the output is given as json.

    python pftpy/algo.py run-all -f "GraphInput:girg" "GirgGen(n=500,d=1,deg=10,seed=50771,ple=2.3,alpha=5.375)" \
    "Algo:part_treedec" "HTD(seed=42,variant=minfill,timeout=300)" "Partition:flc" "Partition:hs" \
    "Partition:branch" "PartitionBags(timeout=10)" "BranchingPartition(timeout=10)" "Output(printer=csv)"

Here, multiple partition solvers are used (greedy, hitting set and branch-and-bound) and the result is printed as csv.
