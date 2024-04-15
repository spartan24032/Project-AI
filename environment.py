# environment.py
import numpy as np

class GridWorld:
    def __init__(self, size, pickups=None, dropoffs=None, dropoffCapacity = 5, proximityPunishment=False, dominantPunishment=False, keyChangeEpisodes=None, flipP=None, flipD=None):
        self.size = size
        self.actions = ['N', 'E', 'S', 'W', 'pickup', 'dropoff']
        self.dropoffStorage = dropoffCapacity
        if pickups is None:
            pickups = {(2, 2): self.dropoffStorage}
        if dropoffs is None:
            dropoffs = {(4, 4): 0}
        self.pickups = pickups
        self.dropoffs = dropoffs
        self.defaultpickups = pickups
        self.defaultdropoffs = dropoffs
        self.flipP = flipP
        self.flipD = flipD
        self.keyChangeEpisodes = keyChangeEpisodes
        self.used_dropoffs = set()
        self.grid = np.zeros((self.size, self.size), dtype=str)
        #self.reset(int)
        self.noops = 0
        self.proximityPunishment = proximityPunishment
        self.dominantPunishment = dominantPunishment
        self.spaceDominance = []


    def get_actions(self):
        return self.actions
    def get_size(self):
        return int(self.size)
    def get_noops(self):
        print(f"no ops: {self.noops}")
        return int(self.noops)
    def get_actions(self):
        return self.actions

    def dropoffs_complete(self):
        return all(capacity == self.dropoffStorage for capacity in self.dropoffs.values())

    def update_influence(self, x, y, agent_id):
        """Increment influence for an agent at a specific grid cell."""
        self.spaceDominance[x][y][agent_id] += 1

    def dominant_agent(self, x, y):
        if x >= len(self.spaceDominance) or y >= len(self.spaceDominance[x]):
            return None
        cell = self.spaceDominance[x][y]
        if not cell:
            return None
        # Get the agent with the maximum influence and the total influence
        max_agent_id = max(cell, key=cell.get)
        max_influence = cell[max_agent_id]
        total_influence = sum(cell.values())

        # Calculate the influence of the second highest to compare
        second_max_influence = max(v for k, v in cell.items() if k != max_agent_id)

        # Check if the maximum influence is significantly greater than the second max
        if max_influence > (second_max_influence + 0.30 * second_max_influence):
            return max_agent_id

    def generate_pd_string(self, usage=0, current_position=None, agents=None, flip=False, agent_id=-1):

        generated_string = ""
        if usage == 0:
            return '5'
        if usage in [1, 3, 5, 7]: # complex_world2 (pd_strings)
            # Generates binary string-- 1 = available pickup/dropoff, 0 = unavailable
            pickups_str = ''.join('1' if capacity > 0 else '0' for capacity in self.pickups.values())
            dropoffs_str = ''.join('1' if count < self.dropoffStorage else '0' for count in self.dropoffs.values())
            generated_string += pickups_str + dropoffs_str
        if usage in [2, 3, 6, 7]: # 8-state proximity checking
            if current_position == None:
                generated_string += 'N0 S0 E0 W0'
            else:
                state, has_item = current_position
                x, y = state
                max_distance = 2  # Check up to two blocks
                if flip:
                    max_distance = 1
                directions = {
                    'N': [(x - i, y) for i in range(1, max_distance + 1)],
                    'S': [(x + i, y) for i in range(1, max_distance + 1)],
                    'E': [(x, y + i) for i in range(1, max_distance + 1)],
                    'W': [(x, y - i) for i in range(1, max_distance + 1)]
                }

                # List of occupied positions based on agents' current states
                occupied_positions = [agent.get_state()[0] for agent in agents if agent.get_state()[0] != current_position]
                proximity_str = ""
                for direction in ['N', 'S', 'E', 'W']:
                    found_agent = '0'
                    for pos in directions[direction]:
                        nx, ny = pos
                        # Check if the position is within grid bounds
                        if 0 <= nx < self.size and 0 <= ny < self.size:
                            # Check if any agent is at the position (nx, ny)
                            if (nx, ny) in occupied_positions:
                                found_agent = '1'
                                break
                    proximity_str += f"{direction}{found_agent} "

                generated_string += proximity_str.strip()
        if usage in [4, 5, 6, 7]: # Pheromone
            if current_position == None or agent_id == -1:
                generated_string += '0'
            else:
                state, has_item = current_position
                x, y = state
                dominant_agent = self.dominant_agent(x, y)
                print(f"agent_id: '{agent_id}', dominant_agent: '{dominant_agent}'")
                if dominant_agent is not None and dominant_agent != agent_id:
                    generated_string += '1'
                else:
                    generated_string += '0'  # Space is non-dominated
                print(f"dominant agent is not None and dominant_agent != agent_id: {generated_string}")

        return generated_string

    def reset(self, episode):
        """
        Resets the environment for a new episode. 
        This includes resetting pickup and dropoff locations + capacaties
        """
        self.noops = 0
        # Reset the grid
        self.pickups = self.defaultpickups
        self.dropoffs = self.defaultdropoffs

        if(self.keyChangeEpisodes is not None):
            if (
                any(start <= episode <= end for start, end in self.keyChangeEpisodes)
                or
                (self.keyChangeEpisodes == [(-2,-2)] and episode %2 == 0)
            ):
                print("using override p/d")
                # During the specified episodes, use the flipped configurations
                if self.flipP is not None:
                    self.pickups = self.flipP
                if self.flipD is not None:
                    self.dropoffs = self.flipD

        self.grid = np.zeros((self.size, self.size), dtype=str)
        # Mark pickups and dropoffs on the grid
        self.used_dropoffs.clear()
        for pickup in self.pickups:
            self.grid[pickup] = 'P'
            self.pickups[pickup] = self.dropoffStorage
        for dropoff in self.dropoffs:
            self.grid[dropoff] = 'D'
            self.dropoffs[dropoff] = 0 # empty dropoffs

    def step(self, agent, action, agents, idx):
        """
        Applies an action taken by an agent and updates environment state

        Returns:
        - reward: The reward resulting from the action.
        """
        if self.spaceDominance == []:
            self.spaceDominance = [[{i: 0 for i in range(len(agents))} for _ in range(self.size)] for _ in range(self.size)]
        current_state, has_item = agent.get_state()
        x, y = current_state
        reward = -1  # Default action cost for moving

        # Determine new position based on the action
        if action == 'N':
            x -= 1
        elif action == 'S':
            x += 1
        elif action == 'E':
            y += 1
        elif action == 'W':
            y -= 1
        new_state = (x, y)

        # Handle pickup/dropoff actions
        if action == 'pickup':
            agent.update_state(current_state, True)
            self.pickups[current_state] -= 1
            reward = 13  # Reward for successful pickup
        elif action == 'dropoff':
            self.dropoffs[current_state] += 1
            agent.update_state(current_state, False)
            reward = 13  # Reward for successful dropoff

        # Get positions of all other agents to check for proximity
        occupied_positions = [other_agent.get_state()[0] for other_agent in agents if other_agent != agent]
        if self.proximityPunishment:
            # Check for adjacent agents and apply penalty
            adjacent_positions = [
                (new_state[0] - 1, new_state[1]),  # North
                (new_state[0] + 1, new_state[1]),  # South
                (new_state[0], new_state[1] - 1),  # West
                (new_state[0], new_state[1] + 1)  # East
            ]
            for pos in adjacent_positions:
                if pos in occupied_positions:
                    reward += -1  # Apply penalty for being adjacent to another agent
        if self.dominantPunishment:
            dominant_agent = self.dominant_agent(x, y)
            if dominant_agent is not None and dominant_agent != idx:
                reward += -1

        # Update agent's position if the action was a move
        if action in ['N', 'S', 'E', 'W']:
            agent.update_state(new_state, has_item)
        self.update_influence(x, y, idx)

        return reward

    def valid_actions(self, agent_state, agents):
        state, has_item = agent_state
        x, y = state
        actions = []

        occupied_positions = [
            (agent.get_state()[0]) for agent in agents
        ]
        # Check movement actions
        if x > 0 and (x - 1, y) not in occupied_positions: actions.append('N')
        if y < self.size - 1 and (x, y + 1) not in occupied_positions: actions.append('E')
        if x < self.size - 1 and (x + 1, y) not in occupied_positions: actions.append('S')
        if y > 0 and (x, y - 1) not in occupied_positions: actions.append('W')
        # pickup and dropoff
        if (x, y) in self.pickups and not has_item and self.pickups[(x, y)] > 0:
            actions.append('pickup')
        if (x, y) in self.dropoffs and has_item and self.dropoffs[(x, y)] < self.dropoffStorage:
            actions.append('dropoff')

        if actions == []: # agent is stuck in a corner, cannot move.
            actions.append('no op')
            self.noops += 1
        return actions

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
