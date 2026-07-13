# Autonomous Volcanic Terrain Exploration Using Markov Decision Process (MDP)

## Short Overview

This repository is for a CSE 440 Artificial Intelligence semester project. The project will study how an autonomous exploration agent can navigate a hazardous volcanic terrain using a Markov Decision Process (MDP).

<p align="center">
  <img src="images/poster.png" alt="Autonomous Volcanic Terrain Exploration project poster" width="850">
</p>

<p align="center">
  <em>Project poster for the autonomous volcanic terrain exploration system.</em>
</p>

The current repository contains the project skeleton, configuration planning, a runnable terrain generator, a core MDP implementation with value iteration, and a baseline comparison experiment that evaluates the MDP explorer against simple agents. Agent movement, full simulation, and visualization features are planned for later weeks.

## Problem Statement

Volcanic environments are dangerous, uncertain, and difficult for humans to explore directly. An autonomous agent operating in this type of environment must make decisions while considering hazards such as lava flows, craters, gas emission zones, and obstacles. At the same time, it should collect useful scientific information and return or remain connected to a base station when needed.

The problem is to design an AI-based exploration system that can decide where the agent should move in a grid-based volcanic terrain while balancing safety, exploration, and scientific reward.

## Why MDP Is Suitable

A Markov Decision Process is suitable for this project because the agent must make sequential decisions under uncertainty. Each movement action may not always lead exactly where intended because of terrain difficulty, sensor limitations, or environmental instability.

An MDP provides a structured way to represent:

- The current state of the agent.
- The possible actions available to the agent.
- The probability of reaching the next state after an action.
- The reward or penalty for entering different terrain cells.
- A policy that recommends the best action for each state.

This makes MDP a good fit for modeling volcanic terrain exploration as a decision-making problem.

## Current and Planned AI Formulation

### States

Each current state represents the agent's position in the terrain grid as `(row, col)`. Rock cells are treated as obstacles and are not included as valid MDP states. A state may later include additional information such as collected science points or changing hazard conditions.

### Actions

The current action set includes `UP`, `DOWN`, `LEFT`, `RIGHT`, `STAY`, and `SCAN`. The `SCAN` action is included as a Week 3 placeholder for later hazard-detection behavior.

### Transition Probabilities

Transition probabilities model uncertainty in movement. The current MDP uses intended movement, left slip, right slip, and stay probabilities. If a movement would go outside the grid or into a rock cell, the agent remains in the same state.

### Rewards

Rewards guide the agent's behavior. Science points and the base station provide positive rewards, while hazardous cells such as lava, craters, and gas zones provide penalties. Invalid blocked movement and scanning also have costs.

### Policy

The policy describes the best planned action for each valid state after value iteration has estimated state values.

### Value Iteration

Value iteration is used as the main algorithm for computing state values and deriving an optimal or near-optimal policy. The first core implementation is included in `support/mdp.py`.

## Planned Volcanic Terrain Elements

- Safe cells: Areas where the agent can move with low risk.
- Lava flows: High-risk areas that should usually be avoided.
- Craters: Dangerous terrain with strong movement or safety penalties.
- Gas emission zones: Hazardous cells that may reduce safety or visibility.
- Rocks/obstacles: Blocked or difficult cells that restrict movement.
- Science points: Valuable locations that the agent should try to explore.
- Base station: The starting location and possible reference point for mission planning.

## Repository Structure

```text
volcanic-mdp-explorer/
|-- main.py
|-- README.md
|-- requirements.txt
|-- .gitignore
|-- data/
|   |-- .gitkeep
|   |-- sample_terrain_seed_42.csv
|   `-- terrain_config.json
|-- support/
|   |-- __init__.py
|   |-- config.py
|   |-- utils.py
|   |-- terrain.py
|   |-- mdp.py
|   |-- agent.py
|   |-- simulation.py
|   |-- visualization.py
|   `-- experiments.py
|-- outputs/
|   `-- .gitkeep
`-- others/
    `-- .gitkeep
```

## Week 1 Progress

- Created the basic repository structure.
- Added a runnable `main.py` setup check.
- Added `requirements.txt` with planned basic libraries.
- Added `data/terrain_config.json` with initial terrain and MDP parameters.
- Added support modules for future terrain, MDP, agent, simulation, visualization, and experiments work.
- Added placeholder files to keep empty folders in Git.
- Confirmed that the current version runs with `python main.py`.

## Week 2 Progress

- Added a volcanic terrain generator in `support/terrain.py`.
- Added configurable grid generation using default config values or command-line size input.
- Added reproducible terrain generation with a random seed.
- Added CSV export for the generated terrain at `data/sample_terrain_seed_42.csv`.
- Prepared the environment structure that will be used for MDP implementation in Week 3.

## Week 3 Progress - MDP Core Implementation

- Implemented the MDP state space using valid non-rock grid cells.
- Added the action set: `UP`, `DOWN`, `LEFT`, `RIGHT`, `STAY`, and `SCAN`.
- Added a stochastic transition model with intended movement, slip, and stay probabilities.
- Added a reward function for safe cells, base, science points, gas, craters, lava, invalid moves, and the scan action.
- Implemented the value iteration algorithm.
- Added optimal policy extraction from computed state values.
- Added basic policy printing and testing from `support/mdp.py`.

## Week 5 Progress - Experiments and Comparison

The experiment module in `support/experiments.py` compares the MDP explorer against two baseline strategies on the same volcanic maps, using multiple random seeds.

- Compared three agents: the MDP policy agent, a random-movement agent, and a greedy nearest-unvisited agent.
- Built the two baselines on top of Member 2's `MDPExplorerAgent` (`support/agent.py`); they are thin subclasses that only change how the next action is chosen, so every agent is measured by the exact same code.
- Ran all three agents over 20 seeded terrains under the same stochastic movement model, so the comparison is fair.
- Used the discount factor `gamma = 0.90` declared in `data/terrain_config.json`.
- Recorded per-run metrics: total reward, coverage percent, hazards entered, science points collected, survival, and total steps.
- Saved one row per run to `outputs/experiment_results.csv` and an averaged bar-chart comparison to `outputs/performance_plot.png`.

The MDP agent follows the value-iteration policy and re-plans after each science sample is collected. Once a sample is gathered its cell becomes ordinary ground, so the agent keeps exploring toward new objectives instead of scoring the same cell repeatedly. Across the 20 terrains the MDP agent earns the highest reward, enters the fewest hazards, collects the most science, and survives most often. The greedy agent covers more ground but walks into far more hazards and dies more often, and the random agent performs worst overall. No MDP, terrain, agent, or simulation code was changed; the experiments only use the existing public methods of those modules.

## Requirements

The current Week 3 Prompt 1 implementation uses only the Python standard library. The following libraries are listed in `requirements.txt` because they are expected to be useful in later stages:

- `numpy`
- `matplotlib`
- `pandas`
- `tqdm`

## Planned Development Roadmap

- Week 1: Planning and repository setup.
- Week 2: Terrain generator.
- Week 3: MDP formulation and value iteration.
- Week 4: Agent simulation and dynamic hazards.
- Week 5: Visualization and comparison experiments.
- Week 6: Demo, report, slides, and final polish.

## How to Run Current Version

Run the current terrain demo with:

```bash
python main.py
```

Optional arguments:

```bash
python main.py --seed 10
python main.py --size 20
python main.py --seed 15 --size 20
```

The program prints the generated terrain grid, cell counts, symbol legend, and saves the terrain to `data/sample_terrain_seed_42.csv`.

Run the Week 3 MDP core implementation test with:

```bash
python support/mdp.py
```

This prints the number of valid MDP states and a basic policy grid. It does not run a full agent simulation yet.

Run the Week 5 experiment comparison with:

```bash
python support/experiments.py
```

This runs the MDP, random, and greedy agents over 20 seeds and writes `outputs/experiment_results.csv` and `outputs/performance_plot.png`.

## Current Limitations

- The project does not yet include a full agent movement simulation module.
- Dynamic hazards are not implemented yet.
- Visualization (`support/visualization.py`) is planned for a later week.
- Final report, slides, demo video, and polished output files are not complete yet.

## Future Outputs

The experiment module now generates these output files when `support/experiments.py` is run:

- `outputs/experiment_results.csv`
- `outputs/performance_plot.png`

The following outputs are still planned for later weeks:

- `final_map.png`
- `demo_video.mp4`

## Team Contribution Placeholder

Team member contributions will be added as the project develops.

| Team Member | Planned Contribution | Status |
| --- | --- | --- |
| Member 1 | Project planning and repository setup | Week 1 complete |
| Member 2 | Terrain generation and configuration | Week 2 complete |
| Member 3 | MDP formulation and value iteration | Week 3 Prompt 1 complete |
| Member 4 | Baseline experiments and performance comparison | Experiments complete |
