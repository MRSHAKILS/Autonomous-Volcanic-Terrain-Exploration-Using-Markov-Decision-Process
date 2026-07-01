"""MDP formulation and value iteration for volcanic terrain exploration.

Week 3 Part 1 focuses on the Markov Decision Process model only:
states, actions, transition probabilities, rewards, value iteration, and policy
extraction. Agent simulation, dynamic hazards, visualization, and experiments
are intentionally left for later weeks.
"""

import sys
from pathlib import Path


# Allow this file to run both as a package module and as a direct script:
#   python -m support.mdp
#   python support/mdp.py
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from support.terrain import BASE, CRATER, GAS, LAVA, ROCK, SAFE, SCIENCE, Terrain


UP = "UP"
DOWN = "DOWN"
LEFT = "LEFT"
RIGHT = "RIGHT"
STAY = "STAY"
SCAN = "SCAN"

MOVEMENT_ACTIONS = [UP, DOWN, LEFT, RIGHT]
ACTIONS = [UP, DOWN, LEFT, RIGHT, STAY, SCAN]

ACTION_DELTAS = {
    UP: (-1, 0),
    DOWN: (1, 0),
    LEFT: (0, -1),
    RIGHT: (0, 1),
}

SLIP_ACTIONS = {
    UP: (LEFT, RIGHT),
    DOWN: (RIGHT, LEFT),
    LEFT: (DOWN, UP),
    RIGHT: (UP, DOWN),
}

CELL_REWARDS = {
    SAFE: -1,
    BASE: 5,
    SCIENCE: 20,
    GAS: -15,
    CRATER: -40,
    LAVA: -100,
}

POLICY_SYMBOLS = {
    UP: "^",
    DOWN: "v",
    LEFT: "<",
    RIGHT: ">",
    STAY: "O",
    SCAN: "?",
}


class VolcanicMDP:
    """Represent the volcanic terrain as a Markov Decision Process."""

    def __init__(self, terrain: Terrain, gamma: float = 0.92) -> None:
        """Create an MDP from an existing terrain grid.

        Args:
            terrain: A generated Terrain object.
            gamma: Discount factor for future rewards.
        """
        self.terrain = terrain
        self.gamma = gamma
        self.states = self._build_states()
        self.values = {state: 0.0 for state in self.states}
        self.policy = {}

    def _build_states(self) -> list[tuple[int, int]]:
        """Create one state for each valid non-rock grid cell."""
        states = []

        for row in range(self.terrain.rows):
            for col in range(self.terrain.cols):
                if self.terrain.get_cell(row, col) != ROCK:
                    states.append((row, col))

        return states

    def get_states(self) -> list[tuple[int, int]]:
        """Return all valid MDP states."""
        return self.states

    def get_actions(self) -> list[str]:
        """Return all available actions."""
        return ACTIONS

    def move(self, state: tuple[int, int], action: str) -> tuple[int, int]:
        """Return the next state after applying one deterministic action.

        If the move goes outside the grid or into a ROCK obstacle, the agent
        remains in the same state.
        """
        if action not in MOVEMENT_ACTIONS:
            return state

        row, col = state
        row_change, col_change = ACTION_DELTAS[action]
        next_row = row + row_change
        next_col = col + col_change

        if not self.terrain.is_valid_position(next_row, next_col):
            return state

        if self.terrain.get_cell(next_row, next_col) == ROCK:
            return state

        return next_row, next_col

    def transition_probabilities(self, state: tuple[int, int], action: str) -> dict[tuple[int, int], float]:
        """Return possible next states and their probabilities.

        Movement actions are stochastic: the agent usually moves as intended,
        but it can slip left, slip right, or stay in place.
        """
        if action == STAY or action == SCAN:
            return {state: 1.0}

        if action not in MOVEMENT_ACTIONS:
            raise ValueError(f"Unknown action: {action}")

        left_slip, right_slip = SLIP_ACTIONS[action]
        movement_outcomes = [
            (self.move(state, action), 0.75),
            (self.move(state, left_slip), 0.10),
            (self.move(state, right_slip), 0.10),
            (state, 0.05),
        ]

        probabilities = {}
        for next_state, probability in movement_outcomes:
            probabilities[next_state] = probabilities.get(next_state, 0.0) + probability

        return probabilities

    def reward(
        self,
        state: tuple[int, int],
        action: str,
        next_state: tuple[int, int],
        visited: set[tuple[int, int]] | None = None,
    ) -> float:
        """Return the reward for taking an action and reaching a next state."""
        if action == SCAN:
            return -2

        if self._is_invalid_blocked_move(state, action, next_state):
            return -5

        next_row, next_col = next_state
        next_cell = self.terrain.get_cell(next_row, next_col)
        reward_value = CELL_REWARDS.get(next_cell, -1)

        if visited is not None:
            if next_state not in visited and next_cell in [SAFE, SCIENCE]:
                reward_value += 8
            elif next_state in visited and next_cell in [SAFE, SCIENCE, BASE]:
                reward_value -= 2

        return reward_value

    def _is_invalid_blocked_move(
        self,
        state: tuple[int, int],
        action: str,
        next_state: tuple[int, int],
    ) -> bool:
        """Check whether the intended movement action was blocked."""
        if action not in MOVEMENT_ACTIONS:
            return False

        return next_state == state and self.move(state, action) == state

    def value_iteration(self, theta: float = 1e-4, max_iterations: int = 1000) -> dict[tuple[int, int], float]:
        """Run value iteration until values converge or the limit is reached."""
        for _ in range(max_iterations):
            largest_change = 0.0
            new_values = self.values.copy()

            for state in self.states:
                old_value = self.values[state]
                action_values = []

                for action in ACTIONS:
                    expected_value = self._calculate_action_value(state, action)
                    action_values.append(expected_value)

                new_values[state] = max(action_values)
                largest_change = max(largest_change, abs(old_value - new_values[state]))

            self.values = new_values

            if largest_change < theta:
                break

        return self.values

    def _calculate_action_value(self, state: tuple[int, int], action: str) -> float:
        """Calculate the expected value of one action from one state."""
        total = 0.0
        transitions = self.transition_probabilities(state, action)

        for next_state, probability in transitions.items():
            immediate_reward = self.reward(state, action, next_state)
            future_value = self.values[next_state]
            total += probability * (immediate_reward + self.gamma * future_value)

        return total

    def extract_policy(self) -> dict[tuple[int, int], str]:
        """Choose the best action for each state using the current values."""
        self.policy = {}

        for state in self.states:
            self.policy[state] = self.best_action(state)

        return self.policy

    def best_action(self, state: tuple[int, int]) -> str:
        """Return the best action for a single state."""
        best_action_name = ACTIONS[0]
        best_action_value = self._calculate_action_value(state, best_action_name)

        for action in ACTIONS[1:]:
            action_value = self._calculate_action_value(state, action)

            if action_value > best_action_value:
                best_action_value = action_value
                best_action_name = action

        return best_action_name

    def print_policy(self) -> None:
        """Print the current policy as a grid of simple action symbols."""
        if not self.policy:
            self.extract_policy()

        for row in range(self.terrain.rows):
            symbols = []

            for col in range(self.terrain.cols):
                cell = self.terrain.get_cell(row, col)

                if cell == ROCK:
                    symbols.append("R")
                else:
                    action = self.policy.get((row, col), STAY)
                    symbols.append(POLICY_SYMBOLS[action])

            print(" ".join(symbols))


# TODO: In Week 3 Part 2, connect the policy to a simple agent decision loop.
# TODO: In later weeks, consider dynamic hazards, visual policy maps, and
# experiment comparisons.


if __name__ == "__main__":
    if __package__ is None or __package__ == "":
        from terrain import Terrain
    else:
        from support.terrain import Terrain

    terrain = Terrain(seed=42)
    terrain.generate()
    mdp = VolcanicMDP(terrain)
    values = mdp.value_iteration()
    policy = mdp.extract_policy()
    print("Number of states:", len(mdp.get_states()))
    print("Sample policy:")
    mdp.print_policy()
