# main.py
from environment import GridWorld
from agent import Agent
from policies import PRandom, PExploit, PGreedy
from runSimulation import run_simulation
import random
import pandas as pd
import numpy as np
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

    complex_world2 = True # This uses a different state for each config of dropoff and pickup.
                            # It is great at finding the optimal policy, but uses 64x memory.
    episode_based = True # This chooses if we are using episodes or steps to run the simulation
                           # False = steps, True = episodes
    #  "r" will either be episodes to run or total steps to run, depending on this value.

    a = env.actions
    agents = [
        # alpha = learning rate , gamma = discount factor
         Agent(a, start_state=(2,2), policy = PExploit, learning_algorithm="Q-learning",alpha=0.3, gamma=0.5),
         Agent(a, start_state=(4,2), policy=PExploit, learning_algorithm="Q-learning",alpha=0.3, gamma=0.5),
        Agent(a, start_state=(0,2), policy=PExploit, learning_algorithm="Q-learning", alpha=0.3, gamma=0.5)
    ]
    sim_control = MockSimulationControl() # This is a mock control class that does nothing, allows code to run without UI
    run_simulation(agents, env, sim_control, complex_world2, episode_based, r=30)
#print(agents[0].Q_dicts['111111'])
excel_writer = pd.ExcelWriter('agents_q_tables_PRANDOM_500_PRANDOM_8500.xlsx', engine='xlsxwriter')

for num, agent in enumerate(agents):
    for q_table in agent.Q_dicts.keys():
        Actions = ['S', 'E', 'W', 'N', 'pickup', 'dropoff']
        cols = ['Location', 'Has_Block', 'S', 'E', 'W', 'N', 'pickup', 'dropoff']
        df = pd.DataFrame(columns=cols)

        for row in range(5):
            for col in range(5):
                location = (row, col)
                for has_block in [True, False]:
                    new_row = {'Location': str(location), 'Has_Block': 1 if has_block else 0}
                    for action in Actions:
                        new_row[action] = round(agent.Q_dicts[q_table].get((location, has_block, action), 0), 2)
                    df.loc[len(df)]= new_row
                    df = df.reset_index(drop=True)

        # Add the DataFrame to the Excel writer object as a new sheet
        sheet_name = 'Agent_{}_{}'.format(num, q_table)
        df.to_excel(excel_writer, sheet_name=sheet_name, index=False)

# Save the Excel writer object
excel_writer.close()

