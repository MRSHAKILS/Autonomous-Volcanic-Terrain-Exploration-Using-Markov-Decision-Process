# Autonomous Volcanic Terrain Exploration Using Markov Decision Process (MDP)

## Project Information

| Item | Details |
| --- | --- |
| Course | CSE 440 — Artificial Intelligence |
| Section | 1 |
| Group | 5 |
| Instructor | Dr. Mohammad Shifat-E-Rabbi [MSRb] |

## Team Members

| Member   | Name           | Primary Responsibility                                                                                   |
| -------- | -------------- | -------------------------------------------------------------------------------------------------------- |
| Member 1 | Shakil Ahmed   | Repository foundation, terrain generation, MDP core, value iteration, policy extraction, and integration |
| Member 2 | Fahim Foysal   | Autonomous agent and simulation                                                                          |
| Member 3 | Shefa Tabassum | Terrain visualization and demo outputs                                                                   |
| Member 4 | Tanvir Ahmed   | Experiments, baseline comparison, and performance analysis                                               |

## Short Overview

This repository is for a CSE 440 Artificial Intelligence semester project. The project studies how an autonomous exploration agent can navigate hazardous volcanic terrain using a Markov Decision Process (MDP).

<p align="center">
  <img src="images/poster.png" alt="Autonomous Volcanic Terrain Exploration project poster" width="850">
</p>

<p align="center">
  <em>Project poster for the autonomous volcanic terrain exploration system.</em>
</p>

Update 1 code from all four members has been merged. The current implementation includes volcanic terrain generation, the core MDP model, value iteration, policy extraction, an MDP-based explorer agent, a simulation loop, terrain visualization, and baseline experiment outputs. Dynamic hazards and final demo/report materials are not complete yet.

## Problem Statement

Volcanic environments are dangerous, uncertain, and difficult for humans to explore directly. An autonomous agent operating in this type of environment must make decisions while considering hazards such as lava flows, craters, gas-emission zones, and obstacles. At the same time, it should collect useful scientific information and remain connected to a base station when needed.

The problem is to design an AI-based exploration system that decides where the agent should move in a grid-based volcanic terrain while balancing safety, exploration, and scientific reward.

## Why MDP Is Suitable

A Markov Decision Process is suitable for this project because the agent must make sequential decisions under uncertainty. Each movement action may not always lead exactly where intended because of terrain difficulty or environmental instability.

An MDP provides a structured way to represent:

- the current state of the agent,
- the possible actions available to the agent,
- the probability of reaching the next state after an action,
- the reward or penalty for entering different terrain cells,
- and a policy that recommends the best action for each state.

## Current AI Formulation

### States

Each state represents the agent's position in the terrain grid as `(row, col)`. Rock cells are treated as obstacles and are excluded from the valid MDP state space.

### Actions

The current action set includes `UP`, `DOWN`, `LEFT`, `RIGHT`, `STAY`, and `SCAN`.

### Transition Probabilities

Transition probabilities model uncertainty in movement. The MDP uses intended movement, left slip, right slip, and stay probabilities. If a movement would go outside the grid or into a rock cell, the agent remains in the same state.

### Rewards

Rewards guide the agent's behavior. Science points and the base station provide positive rewards, while hazardous cells such as lava, craters, and gas zones provide penalties. Invalid blocked movement and scanning also have costs.

### Policy and Value Iteration

Value iteration estimates state values, and the resulting policy selects the best action for each valid state.

## Terrain Symbols

| Character | Meaning               |
| --------- | --------------------- |
| `.`       | Safe traversable cell |
| `L`       | Lava flow             |
| `C`       | Crater                |
| `G`       | Gas-emission zone     |
| `R`       | Rock or obstacle      |
| `S`       | Science point         |
| `B`       | Base station          |

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
|-- images/
|   |-- poster.png
|   |-- terrain_map_seed_1.png
|   |-- terrain_map_seed_7.png
|   `-- terrain_map_seed_23.png
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
|   |-- .gitkeep
|   |-- experiment_results.csv
|   |-- final_map.png
|   `-- performance_plot.png
`-- others/
    `-- .gitkeep
```

## Update 1 Progress

Update 1 code from all four members has been merged.

### Member 1 — MDP Core

- Repository and project structure
- Configuration system
- Volcanic terrain generator
- State and action definitions
- Reward model
- Stochastic transition model
- Value iteration
- Optimal policy extraction

### Member 2 — Agent and Simulation

- `MDPExplorerAgent`
- BASE-position initialization
- Policy-based action selection
- Stochastic movement
- Path and visited-cell tracking
- Reward, hazard, science-point, and survival tracking
- Mission summary and simulation loop

### Member 3 — Visualization

- Matplotlib-based terrain rendering
- Distinct colors for all seven terrain types
- Map title and legend
- Saved visualization output
- Terrain examples generated with different random seeds

### Member 4 — Experiments

- MDP, random, and greedy comparison structure
- Shared experiment metrics
- CSV results generation
- Performance-plot generation

## Generated Results and Visuals

### Exploration Map

![Volcanic terrain exploration map](outputs/final_map.png)

<p align="center">
  <em>Update 1 test visualization of the volcanic terrain. The dashed route is labeled in the image as a sample path for layout testing, not a final autonomous-agent result.</em>
</p>

### Performance Comparison

![Agent performance comparison](outputs/performance_plot.png)

<p align="center">
  <em>Generated comparison visualization for the implemented experiment framework.</em>
</p>

### Terrain Visualization

`support/visualization.py` renders the terrain grid with matplotlib, using a distinct color for each of the seven cell types—Safe, Lava, Crater, Gas, Rock, Science, and Base—together with a title and legend. The following examples were generated using different random seeds.

<table>
  <tr>
    <td align="center">
      <img src="images/terrain_map_seed_1.png" width="300"><br>
      <sub>Terrain Example 1</sub>
    </td>
    <td align="center">
      <img src="images/terrain_map_seed_7.png" width="300"><br>
      <sub>Terrain Example 2</sub>
    </td>
    <td align="center">
      <img src="images/terrain_map_seed_23.png" width="300"><br>
      <sub>Terrain Example 3</sub>
    </td>
  </tr>
</table>

## Requirements

Install the project dependencies with:

```bash
pip install -r requirements.txt
```

The dependency list currently includes:

- `numpy`
- `matplotlib`
- `pandas`
- `tqdm`

## How to Run

Run the terrain demo:

```bash
python main.py
```

Optional terrain arguments:

```bash
python main.py --seed 10
python main.py --size 20
python main.py --seed 15 --size 20
```

Run the MDP core test:

```bash
python support/mdp.py
```

Run the agent demo:

```bash
python support/agent.py
```

Run the simulation loop:

```bash
python support/simulation.py
```

Generate the terrain visualization:

```bash
python support/visualization.py
```

Run the experiment comparison:

```bash
python support/experiments.py
```

## Current Limitations

- Dynamic hazards are not implemented yet.
- The exploration map currently uses a sample/test path, not a final simulation path.
- Final report, slides, demo video, and presentation polish are not complete yet.

## Planned Development Roadmap

- Week 1: Planning and repository setup.
- Week 2: Terrain generator.
- Week 3: MDP formulation and value iteration.
- Week 4: Agent simulation and dynamic hazards.
- Week 5: Visualization and comparison experiments.
- Week 6: Demo, report, slides, and final polish.

## Future Outputs

Generated output files currently include:

- `outputs/experiment_results.csv`
- `outputs/performance_plot.png`
- `outputs/final_map.png`

The following output is still planned for later:

- `demo_video.mp4`
