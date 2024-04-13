# main.py
from environment import GridWorld
from agent import Agent
from policies import PRandom, PExploit, PGreedy
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication, QThread
import sys
from runSimulation import SimulationWorker
import random
from UI import MockSimulationControl

if __name__ == "__main__":
    # Define the environment
    random.seed(5)
    dropoffCapacity = 5
    size = 5
    pickups = {  # {(coordinate): starting capacity}
        (0,2): dropoffCapacity, (1,3): dropoffCapacity, (0,4): dropoffCapacity
                }
    # pickups_alt = { # Alternate pickup locations to change mid-run
    #     (4,2): dropoffCapacity, (3,3): dropoffCapacity, (2,4): dropoffCapacity
    #             }
    dropoffs = {  # {(coordinate): starting inventory}
        (3,0): 0, (2,0): 0, (3,4): 0
    }
    
    env = GridWorld(size, pickups, dropoffs, dropoffCapacity)
    # env = GridWorld(size, pickups, dropoffs, dropoffCapacity, pickups_alt)

    complex_world2 = False  # This uses a different state for each config of dropoff and pickup.
                            # It is great at finding the optimal policy, but uses 64x memory.
    episode_based = False  # This chooses if we are using episodes or steps to run the simulation
                           # False = steps, True = episodes
    #  "r" will either be episodes to run or total steps to run, depending on this value.

    a = env.actions
    agents = [
        # alpha = learning rate , gamma = discount factor
        Agent(a, start_state=(1,1), policy = PRandom, alpha=0.3, gamma=0.5, override_policy=PExploit, override_max_step=500),
        Agent(a, start_state=(4,4), policy=PRandom, alpha=0.3, gamma=0.5, override_policy=PExploit, override_max_step=500),
        Agent(a, start_state=(0,0), policy=PRandom, alpha=0.3, gamma=0.5, override_policy=PExploit, override_max_step=500)
    ]
    r = 6
    sim_control = MockSimulationControl() # This is a mock control class that does nothing, allows code to run without UI
    simulationWorker = SimulationWorker(agents, env, complex_world2, episode_based, r, mskip = True)
    simulationWorker.run_simulation()