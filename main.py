# main.py
from environment import GridWorld
from agent import Agent
from policies import PRandom, PExploit, PGreedy
from runSimulation import run_simulation
import random

if __name__ == "__main__":
    # Define the environment
    random.seed(5)
    dropoffCapacity = 5
    size = 5
    pickups =  {
        (4,1): dropoffCapacity, (1,3): dropoffCapacity, #(0,4): dropoffCapacity
                }  # {(coordinate): starting capacity}
    dropoffs = {
        (0,0): 0, (2,0): 0, #(3,4): 0
    } # {(coordiante): starting inventory}
    
    env = GridWorld(size, pickups, dropoffs, dropoffCapacity)
    
    a = env.actions
    agents = [
        # alpha = learning rate , gamma = discount factor
        Agent(a, start_state=(2,2), policy = PExploit, alpha=0.3, gamma=0.5),
        Agent(a, start_state=(1,1), policy = PExploit, alpha=0.5, gamma=0.3),
        #Agent(a, start_state=(4,4), policy=PExploit, alpha=0.3, gamma=0.5)
    ]

    run_simulation(agents, env, episodes=1000)
