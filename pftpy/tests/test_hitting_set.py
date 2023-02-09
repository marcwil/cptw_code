#!/usr/bin/env python3
import pytest
from random import shuffle
import random
import igraph
from pftpy.actions import ActionContext
from pftpy.graph_actions import hitting_set




@pytest.fixture
def hs_ctx():
    ctx = ActionContext()
    ctx.register_actions(*hitting_set.defined_actions)
    ctx.register_filters("HSBranchReduce(dir=../findminhs)")
    return ctx


def random_instance(n, m, k):
    edges = []
    for _ in range(m):
        nums = []
        while len(nums) < k:
            num = random.randint(0, n-1)
            if num not in nums:
                nums.append(num)
        edges.append(nums)
    return n, edges


def is_solution(instance, solution):
    n, edges = instance
    covered = [False] * len(edges)

    edges_of_vertex = [list() for _ in range(n)]
    for i, edge in enumerate(edges):
        for v in edge:
            edges_of_vertex[v].append(i)

    for chosen in solution:
        for edge in edges_of_vertex[chosen]:
            covered[edge] = True

    return sum(covered) == len(covered)


def test_david_simple(hs_ctx):
    n = 5
    edges = [
        [0, 1],
        [1, 2, 3],
        [1, 4],
        [2, 3],
        [2],
    ]
    instance = (n, edges)
    solver = hs_ctx.construct_action("HSBranchReduce")
    solution = solver(instance)
    print(solution)
    assert len(solution) == 2
    assert 2 in solution
    assert 1 in solution
    assert is_solution(instance, solution)


def test_david_is_solution(hs_ctx):
    n = 30
    for m in [100, 200]:
        for k in [3, 5, 10]:
            instance = random_instance(n, m, k)
            solver = hs_ctx.construct_action("HSBranchReduce")
            solution = solver(instance)
            assert is_solution(instance, solution)


def test_gurobi_simple(hs_ctx):
    n = 5
    edges = [
        [0, 1],
        [1, 2, 3],
        [1, 4],
        [2, 3],
        [2],
    ]
    instance = (n, edges)
    solver = hs_ctx.construct_action("GurobiHS")
    solution = solver(instance)
    print(solution)
    assert len(solution) == 2
    assert 2 in solution
    assert 1 in solution
    assert is_solution(instance, solution)


def test_gurobi_is_solution(hs_ctx):
    n = 30
    for m in [100, 200]:
        for k in [3, 5, 10]:
            instance = random_instance(n, m, k)
            solver = hs_ctx.construct_action("HSBranchReduce")
            solution = solver(instance)
            assert is_solution(instance, solution)


def test_gurobi_eq_david(hs_ctx):
    n = 30
    for m in [100, 200]:
        for k in [3, 5, 10]:
            instance = random_instance(n, m, k)
            david_solver = hs_ctx.construct_action("HSBranchReduce")
            gurobi = hs_ctx.construct_action("GurobiHS")
            solution1 = david_solver(instance)
            solution2 = gurobi(instance)
            print(gurobi._stdout)
            print(gurobi._stderr)
            assert len(solution1) == len(solution2)
