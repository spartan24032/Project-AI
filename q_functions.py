import random
class World:
    def create_world(self):
        grid = [['_' for i in range(5)] for i in range(5)]
        for x,y in self.pick_ups: grid[x][y] = 'P'
        for x,y in self.drop_offs: grid[x][y] = 'D'
        for Agent,Location in self.agents: grid[Location[0]][Location[1]] = Agent
        return grid


    def __init__(self,pk_ups):
        self.pick_ups = pk_ups
        self.drop_offs = [(0,0),(2,0),(3,4)]
        self.agents = [('RD',(2,2)),('BL',(4,2)),('BK',(0,2))]
        self.World_Map= self.create_world()
        self.agent_red = (2,2)
        self.agent_blue = (4,2)
        self.agent_black = (0,2)
    def update_agent_location(self,agent,location):
        if(agent=='RD'):
            self.agent_red = location
        elif(agent =='BL'):
            self.agent_blue = location
        elif(agent =='BK'):
            self.agent_black = location
    def get_agent_location(self,agent):
        if(agent=='RD'):
            return self.agent_red 
        elif(agent =='BL'):
            return self.agent_blue 
        elif(agent =='BK'):
            return self.agent_black 




class State:
    def __init__(self, location):
        self.state_location = location
        self.state_block = 0
        self.q_value = 0
        self.action = None
    def update_state_block(self, block):
        self.state_block =block
    def update_q_value(self,q_val):
        self.q_value = q_val
    def update_action(self,action):
        self.action = action
    def get_location(self):
        return self.state_location
    def get_is_holding(self):
        return self.state_block
    def get_q_value (self):
        return self.q_value
    def get_action(self):
        return self.action
class Grid:
    def __init__(self):
        self.pick_ups_empty = [] #location of all the pickups that are empty
        self.drop_offs_full = [] #locations of all the drop offs pick ups that are full
        self.agent_locations =[]
        self.PD_WORLD = World([(0,4),(1,3),(4,1)])
        self.pick_ups ={ i:0 for i in self.PD_WORLD.pick_ups}
        self.drop_offs ={ i:0 for i in self.PD_WORLD.drop_offs}

    def new_empty_pick_up(self,location):
        self.pick_ups_empty.append(location)
    def new_full_drop_off(self,location):
        self.drop_offs_full.append(location)
    def remove_agent(self,location):
        self.agent_locations.remove(location)
    def add_agent(self,location):
        self.agent_locations.append(location)
    def usable_pickup(self,location):
        if location in self.pick_ups_empty:
            return False
        return True
    def usable_dropoff(self,location):
        if location in self.drop_offs_full:
            return False
        return True
    def not_occupied(self,location):
        if location in self.agent_locations:
            return False
        return True


def print_grid(grid):
    num_rows = len(grid)
    num_cols = len(grid[0])
    print("    ", end="")
    for col_num in range(num_cols):
        print(f"{col_num}".center(5), end="")
        print("|", end="")
    print()

    print("   ", end="")
    print("-" * (5 * num_cols + (num_cols - 1)))
    for row_num, row in enumerate(grid):
        print(f"{row_num}".rjust(2) + " |", end="")
        for cell in row:
            print(str(cell).center(5), end="")
            print("|", end="")
        print()
        print("   ", end="")
        print("-" * (5 * num_cols + (num_cols - 1)))
    print('-'*50)


    
def Next_Move(move,state):
    x,y = state.get_location()
    update_dict = {'N':(0,-1),'S':(0,1),'E':(1,0),'W':(0,1)}
    to_move = update_dict[move]
    return x+to_move[0],y+to_move[1]

def rand_move(state,grid):
    location = state.get_location()
    x,y=-1,-1
    list_to_move = ['N','E','S','W']
    while not (  len(list_to_move)==0 and 0<=x<5 and 0<=y<5  and grid.not_occupied((x,y)) ) :
        move=random.choice(list_to_move)
        list_to_move.remove(move)
        x,y = Next_Move(move,state)
    if(len(list_to_move)==0):
        #none of the points worked 
        return -1,-1
    return x,y
def applicable(state,grid):
    location = state.get_location()


def Q_learning(alpha,gamma,state,action):
    pass

def q_table_finder(state,q_values):
    if (state.get_location()) in q_values:
        return q_values[(state)]
    else:
        q_values[(state)] = 0
        return 0


tracker_Grid = Grid()
dict_states = {}
for agent,location in tracker_Grid.PD_WORLD.agents:
    

    location_of_agent = q_table_finder(location)
    print(location_of_agent.q_value)


    # update_state = rand_move(state,tracker_Grid)
    # state.update_state_location(update_state)
    # x,y= state.get_location()

print_grid(tracker_Grid.PD_WORLD.World_Map)