# environment.py
import numpy as np

class GridWorld:
    def __init__(self, size=5, pickups=None, dropoffs=None):
        self.size = size
        self.actions = ['N', 'E', 'S', 'W', 'pickup', 'dropoff']
        self.pickups = pickups if pickups is not None else [(2, 2)]
        self.dropoffs = dropoffs if dropoffs is not None else [(4, 4)]
        self.used_dropoffs = set()
        self.grid = np.zeros((self.size, self.size), dtype=str)
        self.reset()

    def dropoffs_complete(self):
        return len(self.used_dropoffs) == len(self.dropoffs)

    def reset(self):
        """
        Resets the environment for a new episode. 
        This includes resetting pickup and dropoff locations
        """
        # Reset the grid
        self.grid = np.zeros((self.size, self.size), dtype=str)
        # Mark pickups and dropoffs on the grid
        self.used_dropoffs.clear()
        for pickup in self.pickups:
            self.grid[pickup] = 'P'
        for dropoff in self.dropoffs:
            self.grid[dropoff] = 'D'

    def step(self, agent, action):
        """
        Applies an action taken by an agent and updates environment state

        Parameters:
        - agent: The agent taking the action.
        - action: The action being taken by the agent.

        Returns:
        - reward: The reward resulting from the action.
        """
        current_state, has_item = agent.get_state()
        x, y = current_state
        reward = -0.1  # Default action cost

        # Handling movement actions
        if action == 'N' and x > 0: x -= 1
        elif action == 'S' and x < self.size - 1: x += 1
        elif action == 'E' and y < self.size - 1: y += 1
        elif action == 'W' and y > 0: y -= 1
        elif action in ['pickup', 'dropoff']:
            reward = -1 # Apply penalty if 'pickup' or 'dropoff' is unnecessary

        new_state = (x, y)

        if action == 'pickup' and current_state in self.pickups and not has_item:
            agent.update_state(current_state, True)
            reward = 1  # Reward for valid pickup
        if action == 'dropoff' and agent.get_state()[0] in self.dropoffs and agent.get_state()[1]:
            self.used_dropoffs.add(agent.get_state()[0])
            agent.update_state(current_state, False)
            reward = 10  # Reward for valid dropoff

        # If movement action, update agent's position
        if action in ['N', 'S', 'E', 'W']:
            agent.update_state(new_state, has_item)

        return (agent.get_state()[0], agent.get_state()[1]), reward

    def render(self, agents):
        """
        P = Pickup point
        D = Dropoff point
        A = Agent
        C = Agent (carrying)
        TODO: distinguish agents by index, show capacity (0/5) for pickup and dropoff
        """
        display_grid = np.full((self.size, self.size), fill_value=' ')
    
        # Mark pickups and dropoffs on the display grid
        for pickup in self.pickups:
            display_grid[pickup] = 'P'
        for dropoff in self.dropoffs:
            display_grid[dropoff] = 'D'
    
        # Overlay agents on the grid
        for agent in agents:
            state, has_item = agent.get_state()
            agent_mark = 'C' if has_item else 'A'
            display_grid[state] = agent_mark
    
        # Print the grid
        print("+---" * self.size + "+")
        for row in display_grid:
            print("|", end="")
            for cell in row:
                print(f" {cell} |", end="")
            print("\n" + "+---" * self.size + "+")