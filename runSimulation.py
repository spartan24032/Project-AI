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
        step = -1
        actions_taken = []

        while not (env.dropoffs_complete()):
            step += 1
            if verbose:
                print(f"\nStep {step}")
                env.render(agents)

            actions_taken = []
            for idx, agent in enumerate(agents):
                old_state, old_has_item = agent.get_state()
                # Get valid actions for the CURRENT state, before action is chosen
                valid_actions_current = env.valid_actions(agent.get_state(), agents)
                action = agent.choose_action(valid_actions_current)
                if verbose:
                    print(f"\033[91mAgent {idx}\033[0m {old_state}, Valid Actions: {valid_actions_current}")
                    agents[idx].display_q_values()
                reward = env.step(agent, action)  # Perform the action, moving to the new state
                total_reward += reward
                if verbose:
                    print(f"  selecting: {action}, Reward: {reward}")

                # Now, get valid actions for the NEW state, after action is performed
                new_state, new_has_item = agent.get_state()  # This is effectively 'next_state' for Q-value update
                valid_actions_next = env.valid_actions(agent.get_state(), agents)

                # Update Q-values using 'old_state' as current and 'new_state' as next
                agent.update_q_values(old_state, old_has_item, action, valid_actions_next, reward, new_state,
                                      new_has_item)

                actions_taken.append((idx, action, reward, new_state, valid_actions_current))

                if env.dropoffs_complete():
                    if verbose:
                        print(f"\nStep {step + 1}")
                        env.render(agents)
                        print(f"All dropoffs complete.\nTotal Reward for Episode {episode + 1}: {total_reward}\n")
                    break