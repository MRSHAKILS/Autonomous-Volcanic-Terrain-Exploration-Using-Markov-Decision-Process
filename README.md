# Autonomous Volcanic Terrain Exploration Using Markov Decision Process (MDP)

This repository contains the Week 1 project skeleton for a CSE 440 Artificial Intelligence semester project.

The final goal of the project is to model an autonomous explorer that navigates volcanic terrain using a Markov Decision Process. Week 1 focuses only on repository setup, clean structure, and planning files. The MDP algorithm is not implemented yet.

## Week 1 Scope

- Create a runnable Python project skeleton.
- Add planned folders for data, support modules, outputs, and miscellaneous files.
- Store a basic terrain and MDP configuration in JSON format.
- Add placeholder support modules with docstrings and TODO comments.
- Verify that `python main.py` runs successfully.

## Repository Structure

```text
volcanic-mdp-explorer/
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── .gitkeep
│   └── terrain_config.json
├── support/
│   ├── __init__.py
│   ├── config.py
│   ├── utils.py
│   ├── terrain.py
│   ├── mdp.py
│   ├── agent.py
│   ├── simulation.py
│   ├── visualization.py
│   └── experiments.py
├── outputs/
│   └── .gitkeep
└── others/
    └── .gitkeep
```

## Setup

Create and activate a virtual environment if desired, then install the basic dependencies:

```bash
pip install -r requirements.txt
```

## Run

Run the Week 1 setup check:

```bash
python main.py
```

The script prints the project title, setup status, repository structure status, and next development steps.

## Planned Development

Future work will include terrain generation, MDP state and transition modeling, agent behavior, simulation, visualization, and experiments. These features are intentionally left as TODO items for later weeks.
