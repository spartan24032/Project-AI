# runSimulation.py
import time

def run_simulation(agents, env, sim_control, complex_world2=False, episode_based=True, r=200):

    if episode_based:
        outer_loop = r
    else:
        outer_loop = 1

    for episode in range(outer_loop):
        env.reset()
        pd_string = env.generate_pd_string(complex_world2)
        for agent in agents:
            agent.reset(pd_string)

        # use verbose to control which episodes get output
        # [0, episodes - 1] to see the first and last.
        verbose = episode in [r - 1]

        if verbose:
            print(f"--- Episode {episode + 1} ---")
        if not episode_based:
            print(f"--- Running One Simulation with {r} total steps --- ")
        total_reward = 0
        step = -1
        while( (episode_based == False and step < r) or (episode_based == True and not env.dropoffs_complete()) ):
            #if not episode_based:
            #   verbose = step % 10 == 0
            verbose = step % 1 == 0
            step += 1
            if sim_control.skip_to_step is None:
                sim_control.updateCurrentWorldDisplay(agents, env)
            if verbose:
                print(f"\nStep {step}")
                env.render(agents)

            actions_taken = []
            for idx, agent in enumerate(agents):
                if env.dropoffs_complete():
                    if verbose:
                        print(f"\nStep {step + 1}")
                        env.render(agents)
                        print(f"All dropoffs complete.\nTotal Reward for Episode {episode + 1}: {total_reward}\n")
                    break
                if not episode_based and step > r or env.dropoffs_complete():
                    print("reached max steps OR completed all dropoffs, killing program")
                    exit()
                old_state, old_has_item = agent.get_state()
                # Get valid actions for the CURRENT state, before action is chosen
                valid_actions_current = env.valid_actions(agent.get_state(), agents)
                action = agent.choose_action(valid_actions_current, pd_string)
                if verbose:
                    print(f"\033[91mAgent {idx}\033[0m {old_state}, Valid Actions: {valid_actions_current}")
                    agents[idx].display_q_values(pd_string)
                reward = env.step(agent, action)  # Perform the action, moving to the new state
                total_reward += reward
                pd_string = env.generate_pd_string(complex_world2)
                if verbose:
                    print(f"  selecting: {action}, Reward: {reward}")

                # Now, get valid actions for the NEW state, after action is performed
                new_state, new_has_item = agent.get_state()  # This is effectively 'next_state' for Q-value update
                valid_actions_next = env.valid_actions(agent.get_state(), agents)
                # next_action is only for SARSA as it needs the future action based on policy
                next_action = agent.choose_action(valid_actions_next, pd_string)
                # Update Q-values using 'old_state' as current and 'new_state' as next
                agent.update_q_values(old_state, old_has_item, action, valid_actions_next, reward, new_state,
                                      new_has_item, pd_string, next_action)

                actions_taken.append((idx, action, reward, new_state, valid_actions_current))

            if not sim_control.masterskip:
                # Skip functionality
                if sim_control.skip_to_step is not None:
                    print(f"skip to step/episode enabled, skipping to {sim_control.skip_to_step}")
                    if episode_based and episode >= (int(sim_control.skip_to_step)-1):
                        sim_control.skip_to_step = None  # Reset skipping logic
                    elif not episode_based and step >= (int(sim_control.skip_to_step)-1):
                        sim_control.skip_to_step = None  # Reset skipping logic
                    continue  # Proceed to the next iteration without executing further actions
                if sim_control.autoplay_enabled:
                    print("autoplay enabled")
                    time.sleep(1.0 / sim_control.speedSlider.value()*2)  # Adjust based on the speed slider
                else:
                    print("waiting on next step signal")
                    sim_control.next_step_event.wait()  # Wait for the next step signal
                    sim_control.next_step_event.clear()  # Reset the event for the next iteration
