#!/usr/bin/env python3
from pftpy.actions import ActionContext, Action, ChoiceAction, SequenceAction

import pytest

#        _match_specificity(["a"], ["a"]) == 1
#        _match_specificity(["a"], ["b"]) == 0
#        _match_specificity(["d"], ["a:b:c:d"]) == 1
#        _match_specificity(["c:d"], ["a:b:c:d"]) == 2
#        _match_specificity(["a:c:d"], ["a:b:c:d"]) == 0
@pytest.mark.parametrize("filterstr, call_stack, res", [
    ("a", ["a"], 1),
    ("a", ["b"], 0),
    ("d", ["a", "b", "c", "d"], 1),
    ("c:d", ["a", "b", "c", "d"], 2),
    ("a:c:d", ["a", "b", "c", "d"], 0),
])
def test_context_match_specificity(filterstr, call_stack, res):
    assert ActionContext._match_specificity(filterstr, call_stack) == res


def test_action_parse_parameters():
    f = [
        "a:b:c:d(p1=3)",
        "a:b:c:d(p1,p2,p3=1)",
        "a:b:c:d(p1,p2,p3=1.0)",
        "a:b:c:d(p1=yes,p2=hello)",
    ]
    res = Action.parse_parameters(f)
    assert res[0] == {'p1':'3'}
    assert res[1] == {'p1': True, 'p2': True, 'p3': '1'}
    assert res[2] == {'p1': True, 'p2': True, 'p3': '1.0'}
    assert res[3] == {'p1': 'yes', 'p2': 'hello'}

@pytest.mark.parametrize("filter, res", [
    ("a:b", "b"),
    ("a:b:c", "c"),
    ("a:b(uiae)", "b"),
    ("a:b(p1=v1,p2=v2,p3)", "b"),
    ("a:b:c(p1=v1,p2=v2,p3)", "c"),
])
def test_choice_action_parse_choice(filter, res):
    assert ChoiceAction._parse_choice(filter) == res

class Get1(Action):
    def run(self, _):
        return 1

class Get2(Action):
    def run(self, _):
        return 2

class GetNum(ChoiceAction):
    options = {
        'one': Get1,
        'two': Get2
    }

    @staticmethod
    def default_action():
        return 'one'

class Add5(Action):
    def run(self, num):
        res = num + 5
        self.set_stat('res', res)
        return res

    def get_stat_keys(self, ):
        return ['res']


class Add2(Action):
    def run(self, num):
        res = num + 2
        self._stats('res', res)
        return res

    def get_stat_keys(self, ):
        return ['res']

class Adder(ChoiceAction):
    options = {
        'two': Add2,
        'five': Add5
    }

    @staticmethod
    def default_action():
        return 'two'

class ExampleSeq(SequenceAction):
    steps = [GetNum, Adder]

@pytest.fixture
def context():
    ctx = ActionContext(use_defaults=True)
    ctx.register_actions(ExampleSeq, Adder, Add2, Add5, GetNum, Get1, Get2)
    return ctx

@pytest.fixture
def context_no_default():
    ctx = ActionContext(use_defaults=False)
    ctx.register_actions(ExampleSeq, Adder, Add2, Add5, GetNum, Get1, Get2)
    return ctx

def test_construct_all(context):
    ctx: ActionContext = context
    actions = ctx.construct_variants("ExampleSeq")

    assert len(actions) == 1

def test_construct_all_filtered(context):
    ctx: ActionContext = context
    ctx.register_filters("Adder:two", "Adder:five")

    actions = ctx.construct_variants("ExampleSeq")

    assert len(actions) == 2


def test_construct_all_no_defaults(context_no_default):
    ctx: ActionContext = context_no_default
    actions = ctx.construct_variants("ExampleSeq")

    assert len(actions) == 4

def test_construct_all_no_defaults_filtered(context_no_default):
    ctx: ActionContext = context_no_default
    ctx.register_filters("Adder:two")
    actions = ctx.construct_variants("ExampleSeq")

    assert len(actions) == 2
