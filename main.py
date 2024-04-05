# main.py
from environment import GridWorld
from agent import Agent
from policies import PRandom, PExploit, PGreedy
from runSimulation import run_simulation
import random

if __name__ == "__main__":
    # Define the environment
    # random.seed(5)
    dropoffCapacity = 5
    size = 5
    pickups = {  # {(coordinate): starting capacity}
        (4,1): dropoffCapacity, #(1,3): dropoffCapacity, (0,4): dropoffCapacity
                }
    dropoffs = {  # {(coordinate): starting inventory}
        (0,0): 0, #(2,0): 0, (3,4): 0
    }
    
    env = GridWorld(size, pickups, dropoffs, dropoffCapacity)

    # Create the agents
    complex_world2 = False  # This uses a different state for each config of dropoff and pickup.
                            # It is great at finding the optimal policy, but uses 64x memory.
    a = env.actions
    agents = [
        # alpha = learning rate , gamma = discount factor
        Agent(a, start_state=(2,2), policy = PExploit, alpha=0.3, gamma=0.5),
    ]

    run_simulation(agents, env, complex_world2, episodes=1)
