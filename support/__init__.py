"""Support package for the volcanic MDP explorer project.

The package contains the full pipeline: terrain generation, the MDP core,
the explorer agent, dynamic hazards, the simulation loop, visualization,
demo-video generation, and the baseline experiments.
"""

from support.agent import MDPExplorerAgent
from support.hazards import DynamicHazards
from support.mdp import VolcanicMDP
from support.simulation import Simulation
from support.terrain import Terrain

__all__ = ["DynamicHazards", "MDPExplorerAgent", "Simulation", "Terrain", "VolcanicMDP"]
