# main.py
from environment import GridWorld
from agent import Agent
from policies import PRandom, PExploit, PGreedy

def run_simulation(agents, env, episodes=300):
    
    for episode in range(episodes):
        env.reset()
        for agent in agents:
            agent.reset()
            
        # use verbose to control which episodes get output
        # [0, episodes - 1] to see the first and last.
        verbose = episode in [episodes - 1]  # Verbose output for the first and last episode
        if verbose:
            print(f"--- Episode {episode + 1} ---")
        total_reward = 0
        step = 0

        if verbose:
            print(f"Starting Arrangement, step 0")
            env.render(agents)
            for idx, action, reward, _ in actions_taken:
                print(f"Agent {idx}")
                agents[idx].display_q_values()

        while not(env.dropoffs_complete()):
            step += 1
            actions_taken = []

            for idx, agent in enumerate(agents):
                old_state, old_has_item = agent.get_state()
                valid_actions = env.valid_actions(agent.get_state(), agents)
                action = agent.choose_action(valid_actions)
                (state, has_item), reward = env.step(agent, action)
                total_reward += reward
                actions_taken.append((idx, action, reward, agent.get_state()))
                agent.update_q_values(old_state, old_has_item, action, valid_actions, reward, state, has_item)

                if env.dropoffs_complete():
                    break

            if verbose:
                print(f"Step {step}")
                env.render(agents)

                for idx, action, reward, _ in actions_taken:
                    print(f"\033[91mAgent {idx}\033[0m, Action: {action}, Reward: {reward}")
                    agents[idx].display_q_values()

        if verbose:
            print(f"Total Reward for Episode {episode + 1}: {total_reward}\n")


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
        Agent(a, start_state=(0,0), policy = PExploit, alpha=0.5, gamma=0.1),
        Agent(a, start_state=(1,1), policy = PExploit, alpha=0.7, gamma=0.3)
    ]

    run_simulation(agents, env)