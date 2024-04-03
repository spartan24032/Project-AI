# runSimulation.py

def run_simulation(agents, env, episodes=200):
    actions_taken = []
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

        while not (env.dropoffs_complete()):
            step += 1
            actions_taken = []

            for idx, agent in enumerate(agents):
                old_state, old_has_item = agent.get_state()
                valid_actions = env.valid_actions(agent.get_state(), agents)
                action = agent.choose_action(valid_actions)
                reward = env.step(agent, action)
                total_reward += reward
                actions_taken.append((idx, action, reward, agent.get_state()))
                agent.update_q_values(old_state, old_has_item, action, valid_actions, reward, agent.get_state()[0], agent.get_state()[1])

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