# main.py
from environment import GridWorld
from agent import Agent
from policies import PRandom, PExploit, PGreedy

def run_simulation(agents, env, episodes=200):
    
    for episode in range(episodes):
        env.reset()
        for agent in agents:
            agent.reset()
            
        # use verbose to control which episodes get output
        # [0, episodes - 1] to see the first and last.
        verbose = episode in [episodes - 1]  # Verbose output for the first and last episode
                                                # This can be changed to output none or some episodes if needed
        if verbose:
            print(f"--- Episode {episode + 1} ---")

        total_reward = 0  # track the total reward per episode
        
        i = 0
        while not(env.dropoffs_complete()):
            for agent in agents:
                i = i + 1
                state, has_item = agent.get_state()
                if verbose:
                    print(f"Step {i}, Agent's current state: {state}")
                    agent.display_q_values_for_state(state, has_item)

                valid_actions = env.valid_actions(agent.get_state())
                action = agent.choose_action(valid_actions)
                old_state, old_has_item = agent.get_state()
                (state, has_item), reward = env.step(agent, action)
                total_reward += reward
    
                agent.update_q_values(old_state, old_has_item, action, reward, state, has_item)
    
                if verbose:
                    print(f"Action: {action}, Reward: {reward}")
                    env.render(agents)
                    
                if env.dropoffs_complete():
                    if verbose:
                        print(f"Items successfully dropped off at step {i}. Resetting environment.\n")
                    break

        if verbose:
            print(f"Total Reward for Episode {episode + 1}: {total_reward}\n")
            

if __name__ == "__main__":
    # Define the environment
    dropoffCapacity = 5
    size = 6
    pickups =  {(2, 2): dropoffCapacity}  # coordinate, starting capacity
    dropoffs = {(5,5): 0} # coordiante, starting inventory
    
    env = GridWorld(size, pickups, dropoffs, dropoffCapacity)
    
    a = env.actions
    agents = [ 
        Agent(a, start_state=(0,0), policy = PExploit, epsilon=0.1, alpha=0.1, gamma=0.9),
        
    ]

    run_simulation(agents, env)