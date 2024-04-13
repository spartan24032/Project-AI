# environment.py
import numpy as np

class GridWorld:
    def __init__(self, size, pickups=None, dropoffs=None, dropoffCapacity = 5, pickups_alt=None):
        self.size = size
        self.actions = ['N', 'E', 'S', 'W', 'pickup', 'dropoff']
        self.dropoffStorage = dropoffCapacity
        if pickups is None:
            pickups = {(2, 2): self.dropoffStorage}
        if pickups_alt is None:
            pickups_alt = {}
        if dropoffs is None:
            dropoffs = {(4, 4): 0}
        self.pickups = pickups
        self.pickups_alt = pickups_alt
        self.dropoffs = dropoffs
        self.used_dropoffs = set()
        self.grid = np.zeros((self.size, self.size), dtype=str)
        self.reset()

    def get_actions(self):
        return self.actions
    def get_size(self):
        return int(self.size)

    def dropoffs_complete(self):
        return all(capacity == self.dropoffStorage for capacity in self.dropoffs.values())

    def generate_pd_string(self, usage=False):
        if usage:
            # Generates binary string-- 1 = available pickup/dropoff, 0 = unavailable
            pickups_str = ''.join('1' if capacity > 0 else '0' for capacity in self.pickups.values())
            dropoffs_str = ''.join('1' if count < self.dropoffStorage else '0' for count in self.dropoffs.values())
            return pickups_str + dropoffs_str
        else:
            return '5'

    def reset(self, episode=0):
        """
        Resets the environment for a new episode. 
        This includes resetting pickup and dropoff locations + capacaties
        """
        # Reset the grid
        self.grid = np.zeros((self.size, self.size), dtype=str)
        # Mark pickups and dropoffs on the grid
        self.used_dropoffs.clear()
        if len(self.pickups_alt) > 0 and episode == 3: # If pickups_alt is given, change pickup locations on 4th episode (for experiment 4)
            self.pickups = self.pickups_alt
        for pickup in self.pickups:
            self.grid[pickup] = 'P'
            self.pickups[pickup] = self.dropoffStorage
        for dropoff in self.dropoffs:
            self.grid[dropoff] = 'D'
            self.dropoffs[dropoff] = 0 # empty dropoffs

    def step(self, agent, action):
        """
        Applies an action taken by an agent and updates environment state

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

        return reward
    def valid_actions(self, agent_state, agents):
        state, has_item = agent_state
        x, y = state
        actions = []

        occupied_positions = [
            (agent.get_state()[0]) for agent in agents
        ]

        if x > 0:
            if (x - 1, y) not in occupied_positions: 
                actions.append('N')
        if y < self.size - 1:
            if (x, y + 1) not in occupied_positions: 
                actions.append('E')
        if x < self.size - 1:
            if(x + 1, y) not in occupied_positions:
                actions.append('S')

        if y > 0:
            if (x, y - 1) not in occupied_positions: 
                actions.append('W')
        # pickup and dropoff
        if (x, y) in self.pickups and not has_item and self.pickups[(x, y)] > 0:
            actions.append('pickup')
        if (x, y) in self.dropoffs and has_item and self.dropoffs[(x, y)] < self.dropoffStorage:
            actions.append('dropoff')

        if actions == []: # agent is stuck in a corner, cannot move.
            actions.append('no op')
        return actions

    def blocked_actions(self, agent_state, agents,agent):
        state, has_item = agent_state
        x, y = state
        actions = []
        location =x,y

        occupied_positions = [
            (agent.get_state()[0]) for agent in agents
        ]
        agent_num = {
            (agent.get_state()[0]) :num for num,agent in enumerate(agents)
        }
        could_have = []
        # Check movement actions
        if x > 0:
            if (x - 1, y) in occupied_positions: 
                could_have.append((x-1,y))
        if y < self.size - 1:
            if (x, y + 1)  in occupied_positions: 
                could_have.append((x,y+1))
        if x < self.size - 1:
            if(x + 1, y)  in occupied_positions:
                could_have.append((x+1,y))
        if y > 0:
            if (x, y - 1)  in occupied_positions: 
                could_have.append((x,y-1))

        for blocked_move in could_have:
            if(not has_item and blocked_move in self.pickups and  self.pickups[blocked_move] > 0):
                try:
                    agent.blocked_by[agent_num[blocked_move]].append(('P',(blocked_move)))
                except KeyError:
                    agent.blocked_by[agent_num[blocked_move]]=[('P',(blocked_move))]

            if(has_item and blocked_move in self.dropoffs and self.dropoffs[blocked_move] < self.dropoffStorage):
                try:
                    agent.blocked_by[agent_num[blocked_move]].append(('D',(blocked_move)))
                except KeyError:
                    agent.blocked_by[agent_num[blocked_move]]=[('D',(blocked_move))]
    
    def render(self, agents):
        """
        P/D # = pickup/dropoff, capacity of that location
        A# = Agent, Agent ID
        C# = Agent (carrying), Agent ID
        """
        # ANSI escape codes for colors
        RED = '\033[91m'
        BLUE = '\033[94m'
        ENDC = '\033[0m'  # Resets color to default

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
        print("+----" * self.size + "+")
        for x in range(self.size):
            row_str = ""
            for y in range(self.size):
                cell_content = "    "
                base_content = ''
                if (x, y) in self.pickups:
                    base_content = BLUE + 'P' + str(self.pickups[(x, y)]) + ENDC + '  '
                elif (x, y) in self.dropoffs:
                    base_content = BLUE + 'D' + str(self.dropoffs[(x, y)]) + ENDC + '  '
                else:
                    base_content = '    '
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
                        cell_content = BLUE + f"{base_content[5]}{base_content[6]}" + RED + f"{agent_mark}{agent_id}" + ENDC  # Combine P/D with A/C
                    else:
                        cell_content = RED + f"{agent_mark}{agent_id}" + ENDC + '  ' # Display agent with ID
                else:
                    cell_content = base_content
                row_str += f"|{cell_content:4}"  # Build the row string
            print(row_str + "|")
            print("+----" * self.size + "+")
    def UIrenderVals(self):
        return(
            self.size,
            self.actions,
            self.dropoffStorage,
            self.pickups,
            self.dropoffs,
            self.used_dropoffs
        )
