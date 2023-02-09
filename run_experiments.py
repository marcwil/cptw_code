#!/usr/bin/env python3
from glob import glob
import subprocess
from os import path
import json
from multiprocessing import cpu_count
import run
import pandas as pd

if cpu_count() == 16:
    num = 14
elif cpu_count() == 128:
    num = 120
print(f"Using {num} cores!")
run.use_cores(num)

exp_names = []

def add_experiment(name, filters, params, splitters=None):
    filter_str = " ".join(f'"{fltr}"'for fltr in filters)
    command = f'python pftpy/algo.py run-all -f {filter_str} "Output(printer=csv)"'

    str_splitters = [f"[[{split}]]" for split in splitters]
    file_name = "_".join(str_splitters)
    out_file = f"output_data/{name}/{file_name}.csv"

    run.add(
        name,
        command,
        params,
        stdout_file=out_file,
        header_command=command + ' "CSV(onlyheader,printheader)"'
    )
    exp_names.append(name)

def add_rw_exp(name, filters, params, splitters=None):
    if 'basename' not in params:
        params['basename'] = lambda args: path.basename(args['graph'])
    if splitters is None:
        splitters = []
    splitters.append("basename")
    add_experiment(name, filters, params, splitters)


class RW_Names:
    def __init__(self, persist_path="sizes.json"):
        self.persist_path = persist_path
        if path.exists(persist_path):
            with open(persist_path) as data_file:
                self.data = json.load(data_file)
        else:
            self.data = {}

    def _write_persist(self):
        if not self.persist_path:
            return
        with open(self.persist_path, "w") as data_file:
            json.dump(self.data, data_file)

    def _get_line_count(self, path):
        if path in self.data:
            return self.data[path]
        p = subprocess.run(f"wc -l {path}", shell=True, capture_output=True, text=True)
        num_str = p.stdout.split(" ")[0]
        res = int(num_str)
        self.data[path] = res
        return res

    def get(self, path="./input_data/edge_lists_real/"):
        networks: 'list[str]' = glob(path + "*")
        networks.sort(key=self._get_line_count)
        self._write_persist()
        return networks

    def get_small(self, max_n, max_deg):
        if not path.exists('./output_data/rw_stats.csv'):
            return []
        df = pd.read_csv('./output_data/rw_stats.csv')
        df = df.dropna(axis=1, how='all')
        df = df[df['GraphInput.n'] < max_n]
        df = df[df['GraphStats.avg_deg'] < max_deg]
        df.sort_values('GraphInput.m', inplace=True)
        names = list(df['GraphInput.graph'])
        return [f"./input_data/edge_lists_real/{name}" for name in names]


###
# Experiments
###

###########################
run.group("exp_rw")

Names = RW_Names()
rw_graphs = Names.get()
small_rw = Names.get_small(10000, 30)

add_rw_exp(
    "rw_greedy_ub",
    [
        "GraphInput:readel",
        "ReadEL(path=[[graph]])",
        "Algo:part_treedec",
        "HTD(seed=42,variant=minfill,timeout=300)",
        "Partition:[[partition_solver]]",
    ],
    {
        'graph': rw_graphs,
        'partition_solver': ['lc_repeat', 'flc'],
    },
    ['partition_solver']
)


add_rw_exp(
    "rw_stats",
    [
        "GraphInput:readel",
        "ReadEL(path=[[graph]])",
        "Algo:stats",
        "MaximalCliques:qc",
        "QuickCliques(timeout=10,algo=adjlist)",
    ],
    {
        'graph': rw_graphs,
    },
)

add_rw_exp(
    "rw_ext_vs_heu",
    [
        "GraphInput:readel",
        "ReadEL(path=[[graph]])",
        "Algo:part_treedec",
        f"HTD(seed=42,variant=minfill,timeout={60*5})",
        "Partition:[[partition_solver]]",
        f"PartitionBags(timeout={5*60})",
        f"BranchingPartition(timeout={60*3})",
    ],
    {
        'graph': rw_graphs,
        'partition_solver': ['lc_repeat', 'flc', 'branch']
    },
    ['partition_solver']
)

add_rw_exp(
    "rw_small_ext_vs_heu",
    [
        "GraphInput:readel",
        "ReadEL(path=[[graph]])",
        "Algo:part_treedec",
        f"HTD(seed=42,variant=minfill,timeout={60*5})",
        "Partition:[[partition_solver]]",
        f"PartitionBags(timeout={5*60})",
        f"BranchingPartition(timeout={60*3})",
    ],
    {
        'graph': small_rw,
        'partition_solver': ['lc_repeat', 'flc', 'branch']
    },
    ['partition_solver']
)

# Girg Experiments
run.group("girg")
girg_filters = [
    "GraphInput:girg",
    "GirgGen(n=[[n]],d=[[d]],deg=[[deg]],seed=[[seed]],ple=[[ple]],alpha=[[alpha]])",
]
girg_params_small = {
    'seed': lambda args: args['base_seed']+args['n'],
    'base_seed': list(range(768, 768+2)),
    'n': [500],
    'd': 1,
    'deg': 10,
    'ple': ['2.3', '2.5', '2.7'],
    'alpha': ['inf',
              '5',
              '2.5',
              ],
}
girg_params_large = {
    'seed': lambda args: args['base_seed']+args['n'],
    'base_seed': list(range(768, 768+10)),
    'n': [500, 5000, 50000],
    'd': 1,
    'deg': 10,
    'ple': ['2.1', '2.3', '2.5', '2.7', '2.9'],
    'alpha': ['inf',
              '5',
              '2.5',
              '1.75',
              '1.375',
              '1.25'
              ],
}
if cpu_count() > 20:
    girg_params = girg_params_large
else:
    girg_params = girg_params_small


add_experiment(
    "girg_stats",
    girg_filters + [
        "Algo:stats",
    ],
    girg_params_large,
    [
        "n",
        "ple",
        "alpha"
    ]
)

add_experiment(
    "girg_stats2",
    girg_filters + [
        "Algo:stats2",
        f"HTD(seed=42,variant=minfill,timeout={60*5})",
    ],
    girg_params_large,
    [
        "n",
        "ple",
        "alpha"
    ]
)

add_experiment(
    "girg_flc",
    girg_filters + [
        "Algo:part_treedec",
        f"HTD(seed=42,variant=minfill,timeout={60*5})",
        f"Partition:flc",
    ],
    girg_params,
    [
        "n",
        "ple",
        "alpha"
    ]
)
add_experiment(
    "girg_lcrep",
    girg_filters + [
        "Algo:part_treedec",
        f"HTD(seed=42,variant=minfill,timeout={60*5})",
        f"Partition:lc_repeat"
    ],
    girg_params,
    [
        "n",
        "ple",
        "alpha"
    ]
)
add_experiment(
    "girg_hs",
    girg_filters + [
        "Algo:part_treedec",
        f"HTD(seed=42,variant=minfill,timeout={60*5})",
        "Partition:hs",
        "HittingSet:[[hs_algo]]",
        "PartitionBags(timeout=300)",
        "HSBranchReduce(timeout=180)",
        "GurobiHS(timeout=180)"
    ],
    girg_params | {
        "hs_algo": ["david", "gurobi"]
    },
    [
        "hs_algo",
        "n",
        "ple",
        "alpha"
    ]
)
add_experiment(
    "girg_branch",
    girg_filters + [
        "Algo:part_treedec",
        f"HTD(seed=42,variant=minfill,timeout={60*5})",
        "Partition:branch",
        "PartitionBags(timeout=300)",
        "BranchingPartition(timeout=180)",
    ],
    girg_params,
    [
        "n",
        "ple",
        "alpha"
    ]
)
add_experiment(
    "girg_whs",
    girg_filters + [
        "Algo:part_treedec",
        f"HTD(seed=42,variant=minfill,timeout={60*5})",
        "Partition:whs",
        "HittingSet:gurobi",
        "PartitionBags(timeout=300)",
        "HSBranchReduce(timeout=180)",
        "GurobiHS(timeout=180)"
    ],
    girg_params | {
        "n": [500]
    },
    [
        "n",
        "ple",
        "alpha"
    ]
)

# evaluate branching solver with and without lower bounds
add_experiment(
    "branching_variants_girg",
    girg_filters + [
        "Algo:part_treedec",
        f"HTD(seed=42,variant=minfill,timeout={60*5})",
        "Partition:branch",
        "PartitionBags(timeout=300)",
        "BranchingPartition(timeout=180[[sw_red]][[lb_red]])",
    ],
    girg_params | {
        "sw_red": ["", ",sufficient_weight=false"],
        "lb_red": [",lower_bound2=false,lower_bound=false", ",lower_bound2=false", ""],
    },
    [
        "n",
        "ple",
        "alpha"
    ]
)

add_experiment(
    "branching_variants_girg2",
    girg_filters + [
        "Algo:part_treedec",
        f"HTD(seed=42,variant=minfill,timeout={60*5})",
        "Partition:branch",
        "PartitionBags(timeout=300)",
        "BranchingPartition(timeout=180[[sw_red]][[lb_red]])",
    ],
    girg_params | {
        "alpha": ["5", 'inf'],
        "sw_red": ["", ",sufficient_weight=false"],
        "lb_red": [",lower_bound2=false,lower_bound=false", ",lower_bound2=false", ""],
    },
    [
        "n",
        "ple",
        "alpha"
    ]
)

add_experiment(
    "girg_scaling",
    girg_filters + [
        "Algo:part_treedec",
        f"HTD(seed=42,variant=minfill,timeout={60*5})",
        "Partition:[[partition_solver]]",
        f"PartitionBags(timeout={5*60})",
        f"BranchingPartition(timeout={3*60})",
        f"HSBranchReduce(timeout={3*180})",
        "HittingSet:david",
    ],
    girg_params | {
        'n': [int((1.15)**(i+1)*400) for i in range(35)],
#        'n': [int(4*(i+1)**1.3*100) for i in range(40)],
        'ple': [2.1, 2.5, 2.9],
        'alpha': ['inf', 5, 2.5],
        'partition_solver': ['flc', 'lc_repeat', 'branch', 'hs']
    },
    [
        "partition_solver",
        "n",
        "ple",
        "alpha"
    ]
)


###
# Delete files
###
run.group("delete")
for name in exp_names:
    run.add(
        f"del_csv_{name}",
        f"rm output_data/{name}.csv",
        {}
    )
    run.add(
        f"del_dir_{name}",
        f"rm -r output_data/{name}",
        {}
    )
#    run.add(
#        f"del_pdf_{name}",
#        f"rm output.pdf/{name}*.pdf",
#        {}
#    )

run.run()

###
# Post
###
run.group("post")
run.add(
    "merge_[[exp_name]]",
        f"./merge.sh output_data/[[exp_name]]/ output_data/[[exp_name]].csv",
        {
            'exp_name': exp_names
        },
        creates_file='output_data/[[exp_name]].csv',
)

run.run()
