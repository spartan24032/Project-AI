# main.py
from environment import GridWorld
from agent import Agent

def run_simulation(agents, env, episodes=200):
    
    for episode in range(episodes):
        env.reset()
        for agent in agents:
            agent.reset()
            
        # use verbose to control which episodes get output
        verbose = episode in [0, episodes - 1]  # Verbose output for the first and last episode
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
    
                action, reason = agent.choose_action(state, has_item, verbose=verbose)
                old_state, old_has_item = agent.get_state()
                (state, has_item), reward = env.step(agent, action)
                total_reward += reward
    
                agent.update_q_values(old_state, old_has_item, action, reward, state, has_item)
    
                if verbose:
                    print(f"Action: {action} ({reason}), Reward: {reward}")
                    env.render(agents)
                    
                if env.dropoffs_complete():
                    if verbose:
                        print(f"Items successfully dropped off at step {i}. Resetting environment.\n")
                    break;

        if verbose:
            print(f"Total Reward for Episode {episode + 1}: {total_reward}\n")
            

if __name__ == "__main__":
    # Define the environment
    size = 5
    pickups = [(2, 2)]
    dropoffs = [(4, 4)]
    
    env = GridWorld(size, pickups, dropoffs)
    
    agents = [ 
        Agent(env.actions, start_state=(0,0), epsilon=0.1, alpha=0.1, gamma=0.9),
        
    ]

    run_simulation(agents, env)