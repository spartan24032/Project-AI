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
        reward = -1  # Default action cost

        # Handling movement actions
        if action == 'N': x -= 1
        elif action == 'S': x += 1
        elif action == 'E': y += 1
        elif action == 'W': y -= 1
        elif action == 'pickup':
            agent.update_state(current_state, True)
            reward = 13
        elif action == 'dropoff':
            self.used_dropoffs.add(agent.get_state()[0])
            agent.update_state(current_state, False)
            reward = 13

        new_state = (x, y)

        # If movement action, update agent's position
        if action in ['N', 'S', 'E', 'W']:
            agent.update_state(new_state, has_item)

        return (agent.get_state()[0], agent.get_state()[1]), reward

    def valid_actions(self, agent_state):
        state, has_item = agent_state
        x, y = state
        actions = []
        
        # Add movement actions based on map boundaries
        if x > 0: actions.append('N')
        if y < self.size - 1: actions.append('E')
        if x < self.size - 1: actions.append('S')
        if y > 0: actions.append('W')
            
        # Determine if pickup or dropoff actions are valid
        if (x, y) in self.pickups and not has_item:
            actions.append('pickup')
        if (x, y) in self.dropoffs and has_item:
            actions.append('dropoff')

        return actions

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