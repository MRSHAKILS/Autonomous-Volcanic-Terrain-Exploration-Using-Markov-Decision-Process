# Presentation Slides — Autonomous Volcanic Terrain Exploration Using MDP

> CSE 440 — Artificial Intelligence · Section 1 · Group 5
> One `##` heading per slide; present with any Markdown slide tool (Marp, reveal.js) or copy into PowerPoint.

---

## Slide 1 — Title

**Autonomous Volcanic Terrain Exploration Using Markov Decision Process**

Shakil Ahmed · Fahim Foysal · Shefa Tabassum · Tanvir Ahmed

CSE 440 — Artificial Intelligence, Group 5

---

## Slide 2 — The Problem

- Volcanic terrain is too dangerous for direct human exploration
- An autonomous rover must **explore, collect science samples, and survive**
- Hazards: lava (fatal), craters, gas zones, impassable rock
- Movement is unreliable — the rover can slip sideways or stall
- The environment itself **changes over time**

---

## Slide 3 — Why an MDP?

- Sequential decisions under uncertainty → exactly what MDPs model
- One framework captures:
  - stochastic movement (transition probabilities)
  - hazard costs vs. science rewards (reward function)
  - long-term consequences (discount factor γ)
- Value iteration gives a **provably optimal policy** for the model

---

## Slide 4 — MDP Formulation

- **States:** every non-rock cell `(row, col)` in a 10×10 grid
- **Actions:** UP, DOWN, LEFT, RIGHT, STAY, SCAN
- **Transitions:** 0.75 intended · 0.10 left drift · 0.10 right drift · 0.05 stall
- **Rewards:** science +20 · base +5 · safe −1 · gas −15 · crater −40 · lava −100
- **γ = 0.90**, value iteration to convergence (θ = 10⁻⁴)

---

## Slide 5 — System Pipeline

1. Seeded terrain generation (`terrain.py`)
2. Value iteration + policy extraction (`mdp.py`)
3. Policy-following stochastic agent (`agent.py`)
4. Simulation loop with termination rules (`simulation.py`)
5. Mission map + animated demo (`visualization.py`, `demo_video.py`)

`python main.py` runs the whole pipeline end to end

---

## Slide 6 — Collect-Once + Re-Planning

- Naive MDP behavior: **camp forever** on one +20 science cell
- Our rule: a sample is collected **once**, the cell becomes ordinary ground
- The agent immediately **re-runs value iteration** → heads to the next objective
- Result: purposeful multi-objective missions instead of reward farming

---

## Slide 7 — Dynamic Hazards

- Gas clouds **drift** into neighboring safe cells (p = 0.15 / cloud / step)
- Lava **spills** into neighboring safe cells (p = 0.08), cools back after 6 steps
- Base, science, rock, crater cells are never destroyed → state space stays fixed
- Every terrain change triggers a **fresh re-plan**
- A lava flow reaching the rover destroys it

---

## Slide 8 — Experimental Setup

- 3 agents, identical environment and rules, only action selection differs:
  - **MDP** — value-iteration policy + re-planning
  - **Greedy** — BFS to nearest unvisited cell (ignores soft hazards)
  - **Random** — uniform random direction
- 20 random terrains (seeds 0–19), ≤100 steps each

---

## Slide 9 — Results

| Agent  | Reward     | Coverage % | Hazards | Science | Survival % |
| ------ | ---------- | ---------- | ------- | ------- | ---------- |
| MDP    | **+42.0**  | 13.9       | **1.9** | **3.5** | **60%**    |
| Greedy | −124.5     | **29.3**   | 9.0     | 2.9     | 30%        |
| Random | −179.5     | 7.6        | 3.8     | 0.7     | 15%        |

- Only the MDP agent earns **positive reward**
- 2× the survival of greedy with ~5× fewer hazard entries

---

## Slide 10 — Takeaways & Future Work

- Decision-theoretic planning beats heuristics in hazardous exploration
- Safety and science emerge from the reward model — no hand-coded rules
- Future: risk-sensitive objectives, richer state (energy, remaining science), POMDP with fog-of-war `SCAN`

**Demo:** `images/demo_video.gif` — full mission under dynamic hazards
