from ortools.linear_solver import pywraplp
from .NotifyUserException import NotifyUserException
from typing import List
import math
import itertools


class PackItem:
    def __init__(self, identity: str, width: int, height: int):
        self.identity = identity
        self.width = width
        self.height = height


class TileRow:
    def __init__(self, tiles: List[PackItem], height: int):
        self.tiles = tiles
        self.height = height


class PackGrid:
    def __init__(self, tiles: List[TileRow], width: int, height: int):
        self.width = width
        self.height = height
        self.tiles = tiles


def pack_items(items: List[PackItem]):
    # Simple ORTools based packer that optimizes based on width
    # TODO: Implement a 2D bin packer
    item_ids = list(range(len(items)))
    bin_capacity = 0
    for item in items:
        if item.width > bin_capacity:
            bin_capacity = item.width
    bins = list(range(len(item_ids)))
    solver = pywraplp.Solver.CreateSolver('bin_packing_mip', 'CBC')

    # Variables
    # x[i, j] = 1 if item i is packed in bin j.
    x = {}
    for i in item_ids:
        for j in bins:
            x[(i, j)] = solver.IntVar(0, 1, 'x_%i_%i' % (i, j))

    # y[j] = 1 if bin j is used.
    y = {}
    for j in bins:
        y[j] = solver.IntVar(0, 1, 'y[%i]' % j)

    # Constraints
    # Each item must be in exactly one bin.
    for i in item_ids:
        solver.Add(sum(x[i, j] for j in bins) == 1)

    # The amount packed in each bin cannot exceed its capacity.
    for j in bins:
        solver.Add(
            sum(x[(i, j)] * items[i].width for i in item_ids) <= y[j] *
            bin_capacity)

    # Objective: minimize the number of bins used.
    solver.Minimize(solver.Sum([y[j] for j in bins]))

    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        raise NotifyUserException("Could not find optimal solution for packing")

    output_bins = []
    for j in bins:
        if y[j].solution_value() == 1:
            bin_items: List[PackItem] = []
            for i in item_ids:
                if x[i, j].solution_value() > 0:
                    bin_items.append(items[i])
            if len(bin_items) > 0:
                output_bins.append(bin_items)

    return_set = []
    tile_x = math.ceil(math.sqrt(len(output_bins)))
    max_height = 0
    total_height = 0
    temp_set = []
    for output_bin in output_bins:
        if len(temp_set) == tile_x:
            return_set.append(TileRow(list(itertools.chain.from_iterable(temp_set)), max_height))
            temp_set = []
            total_height += max_height
            max_height = 0
        temp_set.append(output_bin)
        for img in output_bin:
            if img.height > max_height:
                max_height = img.height
    if len(temp_set) > 0:
        return_set.append(TileRow(list(itertools.chain.from_iterable(temp_set)), max_height))
        total_height += max_height
    return PackGrid(return_set, width=tile_x*bin_capacity, height=total_height)
