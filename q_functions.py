import random
class World:
    def create_world(self):
        grid = [['_' for i in range(5)] for i in range(5)]
        for x,y in self.pick_ups: grid[x][y] = 'P'
        for x,y in self.drop_offs: grid[x][y] = 'D'
        for Agent,Location in self.agents.items(): grid[Location[0]][Location[1]] = Agent
        return grid


    def __init__(self,pk_ups):
        self.pick_ups = pk_ups
        self.drop_offs = [(0,0),(2,0),(3,4)]
        self.agents = {'RD':(2,2),'BL':(4,2),'BK':(0,2)}
        self.World_Map= self.create_world()

class States:
    def __init__(self):
        self.states ={}
    def add_state (self,location,holding_block,action):
        if ((location,holding_block,action) in self.states):
            pass

class Grid:
    def __init__(self):
        self.PD_WORLD = World([(0,4),(1,3),(4,1)])
        self.pick_ups_empty = [] #location of all the pickups that are empty
        self.drop_offs_full = [] #locations of all the drop offs pick ups that are full
        self.agent_locations =self.PD_WORLD.agents
        self.pick_ups ={ i:0 for i in self.PD_WORLD.pick_ups}
        self.drop_offs ={ i:0 for i in self.PD_WORLD.drop_offs}
    def Update_World_Map(self,agent,old_location,new_location):
        r,c = old_location
        if old_location in self.pick_ups:
            self.PD_WORLD.World_Map[r][c] = 'P'
        elif old_location in self.drop_offs:
            self.PD_WORLD.World_Map[r][c] = 'D'
        else:
            self.PD_WORLD.World_Map[r][c] = '_'
        rn,cn = new_location
        if new_location in self.pick_ups:
            self.PD_WORLD.World_Map[rn][cn] = agent+' P'
        elif new_location in self.drop_offs:
            self.PD_WORLD.World_Map[rn][cn] = agent+' D'
        else:
            self.PD_WORLD.World_Map[rn][cn] = agent

    def update_agent(self,agent,new_location):
        old_location = self.agent_locations[agent]

        self.agent_locations[agent] = new_location
        self.Update_World_Map(agent,old_location,new_location)

        

        
        
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
        if location in self.agent_locations.values():
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


    
def Next_Move(move,location):
    x,y = location
    update_dict = {'N':(0,-1),'S':(0,1),'E':(1,0),'W':(0,1)}
    to_move = update_dict[move]
    return x+to_move[0],y+to_move[1]

def rand_move(location,grid):
    x,y=-1,-1
    list_to_move = ['N','E','S','W']
    while not ( 0<=x<5 and 0<=y<5  and grid.not_occupied((x,y)) ) :
        if(len(list_to_move)==0):
            return -1,-1
        move=random.choice(list_to_move)
        list_to_move.remove(move)
        x,y = Next_Move(move,location)
    return x,y


# def q_table_finder(agent,location):
#     if (state.get_location()) in q_values:
#         return q_values[(state)]
#     else:
#         q_values[(state)] = 0
#         return 0


tracker_Grid = Grid()
Q_tables = {'RD':{},'BL':{},'BK':{}}
print_grid(tracker_Grid.PD_WORLD.World_Map)
for i in range(100):
    for agent,location in tracker_Grid.PD_WORLD.agents.items():
        print(agent,location)
        can_move = rand_move(location,tracker_Grid)
        if(-1 == can_move[0]):
            continue
        else:
            tracker_Grid.update_agent(agent,can_move)
            print_grid(tracker_Grid.PD_WORLD.World_Map)
