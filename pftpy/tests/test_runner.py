#!/usr/bin/env python3
from pftpy.actions import Action, SequenceAction, ActionContext
from pftpy.runner import Runner

import pytest

class NumberGen(Action):
    def __init__(self, context, parents, params):
        super().__init__(context, parents, params)

    def run(self, input):
        n = int(self._params['n'])

        res = list(range(n))
        self._stats['sum'] = sum(res)
        return res

    @staticmethod
    def name() -> 'str':
        return "NumberGen"

    @staticmethod
    def default_params():
        return {'n': 4}

    def stats(self) -> 'dict[str,str]':
        return self._stats

    def get_stat_keys(self) -> 'list[str]':
        return super().get_stat_keys() + ['sum']

class Adder(Action):
    def __init__(self, context, parents, params):
        super().__init__(context, parents, params)

    def run(self, input):
        num = int(self._params['num'])
        res = []
        for n in input:
            res.append(int(n) + num)

        avg = sum(res) / len(res)
        self.set_stat('avg', avg)
        return res

    def get_stat_keys(self):
        return super().get_stat_keys() + ['avg']

    @staticmethod
    def name() -> 'str':
        return "Adder"

    @staticmethod
    def default_params():
        return {'num': 10}


class ListAdd(SequenceAction):
    steps = [NumberGen, Adder]

    @staticmethod
    def name() -> 'str':
        return "ListAdd"

@pytest.fixture
def example_runner():
    action_name = "ListAdd"
    actions = [ListAdd, NumberGen, Adder]

    runner = Runner(action_name, *actions)
    return runner

def test_runner_run_default(example_runner):
    res = list(example_runner.run())
    first_line = res[0]
    assert first_line.startswith("11.5")

def test_runner_run_multiple(example_runner):
    res = list(example_runner.run_all(["Adder(num=1)", "Adder(num=20)"]))
    assert len(res) == 2
    assert res[0].startswith("2.5")
    assert res[1].startswith("21.5")

def test_output_csv(example_runner):
    res = list(example_runner.run(["Output(printer=csv)", "CSV(printheader)"]))

    assert len(res) == 2
    assert "," in res[0]
    assert res[0].startswith("Adder.avg,")

def test_output_json(example_runner):
    res = list(example_runner.run(["Output(printer=json)",]))

    assert '"NumberGen.sum": 6' in res[0]
