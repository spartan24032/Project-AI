# main.py
from environment import GridWorld
from agent import Agent
from policies import PRandom, PExploit, PGreedy
from runSimulation import run_simulation
import random
from UI import MockSimulationControl

if __name__ == "__main__":
    # Define the environment
    random.seed(5)
    dropoffCapacity = 5
    size = 5
    pickups = {  # {(coordinate): starting capacity}
        (1,3): dropoffCapacity, (4,1): dropoffCapacity, (0,4): dropoffCapacity
                }
    dropoffs = {  # {(coordinate): starting inventory}
        (0,0): 0, (2,0): 0, (3,4): 0
    }
    
    env = GridWorld(size, pickups, dropoffs, dropoffCapacity)

    complex_world2 = True  # This uses a different state for each config of dropoff and pickup.
                            # It is great at finding the optimal policy, but uses 64x memory.
    episode_based = False  # This chooses if we are using episodes or steps to run the simulation
                           # False = steps, True = episodes
    #  "r" will either be episodes to run or total steps to run, depending on this value.

    a = env.actions
    agents = [
        # alpha = learning rate , gamma = discount factor
         Agent(a, start_state=(2,2), policy = PRandom, learning_algorithm="Q-learning",alpha=0.3, gamma=0.5),
         Agent(a, start_state=(4,2), policy=PRandom, learning_algorithm="Q-learning",alpha=0.3, gamma=0.5),
        Agent(a, start_state=(0,2), policy=PRandom, learning_algorithm="Q-learning", alpha=0.3, gamma=0.5)
    ]
    sim_control = MockSimulationControl() # This is a mock control class that does nothing, allows code to run without UI
    run_simulation(agents, env, sim_control, complex_world2, episode_based, r=30)
    Actions =['S','E','W','N','P','D']
    Agent_Action_State = dict()
    for num,agent in enumerate(agents):
        #print(num)
        for dict_agent in agent.Q_dicts.keys():
            for element in agent.Q_dicts[dict_agent]:
                Action = element[2]
                Q_value = agent.Q_dicts[dict_agent][element]
                try:
                    Agent_Action_State[(dict_agent,Action)].append((element,Q_value))
                except KeyError:
                    Agent_Action_State[(dict_agent,Action)] =[(element,Q_value)]
All_S = Agent_Action_State[('111111', 'S')]
All_S.sort( key = lambda x:x[0][0])
for element in All_S:
    print(element[0][0],round(element[1],2))

