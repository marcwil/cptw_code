# CPTW Code

*Code and plotting scripts for paper TODO:TITLE*

## Preparation

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

## Running experiments

Experiments are defined in `run_experiments.py` and experiment results are
written to `output_data`.

To run all experiments, execute `./run_all_experiments.sh`.

To run a specific experiment (e.g. `girg_scaling`) execute `python
run_experiments.py girg_scaling` and then `python run_experiments.py post`.

## Plotting

Plotting scripts are under `plotting`, can be called using `Rscript
<script_name.R>` and write the resulting PDFs into the directory `./output.pdf`.

To run all plotting scripts, execute `./generate_plots.sh`.
