# environment.py
import numpy as np

class GridWorld:
    def __init__(self, size=5, pickups=None, dropoffs=None, dropoffCapacity = 5):
        self.size = size
        self.actions = ['N', 'E', 'S', 'W', 'pickup', 'dropoff']
        self.dropoffStorage = dropoffCapacity
        if pickups is None:
            pickups = {(2, 2): self.dropoffStorage}
        if dropoffs is None:
            dropoffs = {(4, 4): 0}
        self.pickups = pickups
        self.dropoffs = dropoffs
        self.used_dropoffs = set()
        self.grid = np.zeros((self.size, self.size), dtype=str)
        self.reset()

    def dropoffs_complete(self):
        return all(capacity == self.dropoffStorage for capacity in self.dropoffs.values())

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
            self.pickups[pickup] = self.dropoffStorage
        for dropoff in self.dropoffs:
            self.grid[dropoff] = 'D'
            self.dropoffs[dropoff] = 0 # empty dropoffs

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
            self.pickups[current_state] -= 1
            reward = 13
        elif action == 'dropoff':
            self.dropoffs[current_state] += 1
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
        if (x, y) in self.pickups and not has_item and self.pickups[(x, y)] > 0:
            actions.append('pickup')
        if (x, y) in self.dropoffs and has_item and self.dropoffs[(x, y)] < self.dropoffStorage:
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
        print("+----" * self.size + "+")  # Correctly add horizontal lines
        for x in range(self.size):
            row_str = ""
            for y in range(self.size):
                # Initialize cell as empty
                cell_content = "    "
                # Determine if the cell is a pickup or dropoff
                base_content = ''
                if (x, y) in self.pickups:
                    base_content = 'P' + str(self.pickups[(x, y)])
                elif (x, y) in self.dropoffs:
                    base_content = 'D' + str(self.dropoffs[(x, y)])
                else:
                    base_content = '    '
                # Check for agent in this cell
                agent_here = False
                for idx, agent in enumerate(agents):
                    agent_state, has_item = agent.get_state()
                    if agent_state == (x, y):
                        agent_mark = 'C' if has_item else 'A'
                        agent_id = str(idx)
                        agent_here = True
                        break
                if agent_here:
                    if base_content.strip():  # If pickup/dropoff
                        cell_content = f"{base_content[0]}{agent_mark}"  # Combine P/D with A/C
                    else:
                        cell_content = f"{agent_mark}{agent_id}"  # Display agent with ID
                else:
                    cell_content = base_content  # No agent, just show the location status
                row_str += f"|{cell_content:4}"  # Build the row string
            print(row_str + "|")
            print("+----" * self.size + "+")