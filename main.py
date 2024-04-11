# main.py
from environment import GridWorld
from agent import Agent
from policies import PRandom, PExploit, PGreedy
from runSimulation import run_simulation
import random
from UI import MockSimulationControl

from UI import SimulationControl
import sys
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)  # Create an instance of QApplication

    # Define the environment
    random.seed(5)
    dropoffCapacity = 5
    size = 5
    pickups = {  # {(coordinate): starting capacity}
        (0,2): dropoffCapacity, (1,3): dropoffCapacity, (0,4): dropoffCapacity
                }
    dropoffs = {  # {(coordinate): starting inventory}
        (3,0): 0, (2,0): 0, (3,4): 0
    }
    
    env = GridWorld(size, pickups, dropoffs, dropoffCapacity)

    complex_world2 = True  # This uses a different state for each config of dropoff and pickup.
                            # It is great at finding the optimal policy, but uses 64x memory.
    episode_based = True  # This chooses if we are using episodes or steps to run the simulation
                           # False = steps, True = episodes
    #  "r" will either be episodes to run or total steps to run, depending on this value.

    a = env.actions
    agents = [
        # alpha = learning rate , gamma = discount factor
        Agent(a, start_state=(0,0), policy=PExploit, learning_algorithm="Q-learning", alpha=0.7, gamma=0.8),
        #Agent(a, start_state=(1,1), policy = PExploit, alpha=0.5, gamma=0.3),
        #Agent(a, start_state=(4,4), policy=PExploit, alpha=0.3, gamma=0.5)
    ]
    # sim_control = MockSimulationControl() # This is a mock control class that does nothing, allows code to run without UI
    sim_control = SimulationControl() # This is a mock control class that does nothing, allows code to run without UI
    sim_control.show()  # Show the main window
    sys.exit(app.exec_())  # Start the event loop and wait for exit
    run_simulation(agents, env, sim_control, complex_world2, episode_based, r=300)