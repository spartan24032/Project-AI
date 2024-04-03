# main.py
from environment import GridWorld
from agent import Agent
from policies import PRandom, PExploit, PGreedy
from runSimulation import run_simulation

if __name__ == "__main__":
    # Define the environment
    dropoffCapacity = 5
    size = 5
    pickups =  {(2, 2): dropoffCapacity, (3,3): dropoffCapacity}  # {(coordinate): starting capacity}
    dropoffs = {(4,4): 0, (4,0): 0} # {(coordiante): starting inventory}
    
    env = GridWorld(size, pickups, dropoffs, dropoffCapacity)
    
    a = env.actions
    agents = [
        # alpha = learning rate , gamma = discount factor
        Agent(a, start_state=(0,0), policy = PExploit, alpha=0.5, gamma=0.3),
        Agent(a, start_state=(1,1), policy = PExploit, alpha=0.5, gamma=0.3)
    ]

    run_simulation(agents, env, episodes=200)