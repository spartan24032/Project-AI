# runSimulation.py
import time
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QTimer
import copy

class SimulationWorker(QObject):
    finished = pyqtSignal()
    # self.agents, env, episode, step, self.r, episode_based, totalsteps
    update_display = pyqtSignal(object, object, int, int, int, bool, int)
    # idx, agent_buffer, valid_actions_current, pd_string_buffer (list), action, reward
    update_qtable_display = pyqtSignal(int, object, list, list, str, float)
    # total_steps, total_reward, total_collisions
    episode_end = pyqtSignal(float, float, int)
    requestPause = pyqtSignal()
    requestPlay = pyqtSignal(int)
    requestNext = pyqtSignal()
    requestSkip = pyqtSignal(int)

    def __init__(self, agents, env, complex_world2, episode_based, r, mskip):
        super().__init__()
        self.agents = agents
        self.env = env
        self.additional_state = complex_world2 # 0 - none, 1 - complex_world2, 2- 8-state proximity
        self.episode_based = episode_based
        self.r = r
        self.paused = True
        self.moveOne = 0
        self.skipTo = None
        self.autoPlay = False
        self.autoPlay_speed = 1
        self.requestPause.connect(self.onPause)
        self.requestPlay.connect(self.onPlay)
        self.requestNext.connect(self.onNext)
        self.requestSkip.connect(self.onSkip)
        self.mskip = mskip
        self.totalsteps = 0

    def onPause(self):
        self.paused = True

    def onPlay(self, speed):
        self.paused = False
        self.autoPlay = True
        self.autoPlay_speed = speed

    def onNext(self):
        self.moveOne = self.moveOne + 1

    def onSkip(self, targetN):
        self.skipTo = targetN
        self.paused = True

    def run_simulation(self):
        episode = 0
        if self.episode_based:
            for _ in range(self.r):
                episode = self.core_logic(episode)
        else:
            while self.totalsteps < self.r:
                episode = self.core_logic(episode)

        self.finished.emit()
    def core_logic(self, episode):
        episode += 1
        self.blockage_count = 0
        self.env.reset(episode)
        pd_string = self.env.generate_pd_string(self.additional_state)
        next_pd_buffer = []
        for agent in self.agents:
            next_pd_buffer.append(pd_string)
            agent.reset(pd_string)

        # use verbose to control which episodes get output
        # [0, self.r - 1] to see the first and last.
        verbose = episode in [self.r - 1]

        if verbose:
            print(f"--- Episode {episode + 1} ---")

        total_reward = 0
        step = 0
        while (not self.env.dropoffs_complete()):
            if not self.episode_based:
                verbose = step % 60 == 0
                if self.totalsteps > self.r:
                    return episode

            if verbose:
                print(f"\nStep {step}")
                self.env.render(self.agents)
            if self.skipTo is None:
                agent_buffer = copy.deepcopy(self.agents)
                environment_buffer = copy.deepcopy(self.env)

                pd_buffer = copy.deepcopy(next_pd_buffer)
                next_pd_buffer = []
                self.update_display.emit(
                    agent_buffer, environment_buffer, episode, step, self.r, self.episode_based, self.totalsteps
                )
            actions_taken = []

            for idx, agent in enumerate(self.agents):
                if verbose:
                    print(f"\nStep {step + 1}")
                    self.env.render(self.agents)
                    print(f"All dropoffs complete.\nTotal Reward for Episode {episode + 1}: {total_reward}\n")
                pd_string = self.env.generate_pd_string(self.additional_state, agent.get_state(), self.agents)
                old_state, old_has_item = agent.get_state()
                # Get valid actions for the CURRENT state, before action is chosen
                valid_actions_current = self.env.valid_actions(agent.get_state(), self.agents)
                action = agent.choose_action(valid_actions_current, pd_string, step, episode, self.episode_based)
                self.check_for_blockages(agent, valid_actions_current, pd_string)
                if verbose:
                    print(f"\033[91mAgent {idx}\033[0m {old_state}, Valid Actions: {valid_actions_current}")
                    self.agents[idx].display_q_values(pd_string)
                reward = self.env.step(agent, action, self.agents)  # Perform the action, moving to the new state
                pd_string = self.env.generate_pd_string(self.additional_state, agent.get_state(), self.agents)
                step += 1
                self.totalsteps += 1
                total_reward += reward
                if verbose:
                    print(f"  selecting: {action}, Reward: {reward}")
                if self.skipTo is None:
                    self.update_qtable_display.emit(idx, agent_buffer, valid_actions_current, pd_buffer, action, reward)

                # Now, get valid actions for the NEW state, after action is performed
                new_state, new_has_item = agent.get_state()  # This is effectively 'next_state' for Q-value update
                packed_state = new_state, new_has_item
                valid_actions_next = self.env.valid_actions(agent.get_state(), self.agents)
                new_pd_string = self.env.generate_pd_string(self.additional_state, packed_state, self.agents)
                # next_action is only for SARSA as it needs the future action based on policy
                next_action = agent.choose_action(valid_actions_next, new_pd_string, step, episode, self.episode_based)
                # Update Q-values using 'old_state' as current and 'new_state' as next
                agent.update_q_values(old_state, old_has_item, action, valid_actions_next, reward, new_state,
                                      new_has_item, new_pd_string, next_action)

                actions_taken.append((idx, action, reward, new_state, valid_actions_current))
                next_pd_buffer.append(pd_string)
                # check_for_blockages(self, agent, valid_actions, pd_string)

            """for idx, agent in enumerate(self.agents):
                pd_string = self.env.generate_pd_string(self.additional_state, agent.get_state(), self.agents)
                next_pd_buffer.append(pd_string)"""
            if not self.mskip:
                if self.skipTo is not None:
                    if self.episode_based and episode > (int(self.skipTo) - 1):
                        self.skipTo = None  # Reset skipping logic
                    elif not self.episode_based and self.totalsteps > (int(self.skipTo) - 1):
                        self.skipTo = None  # Reset skipping logic
                    continue
                if self.paused:
                    while self.paused:
                        time.sleep(0.1)
                        if (self.moveOne > 0):
                            self.moveOne = self.moveOne - 1
                            break
                if self.autoPlay:
                    time.sleep((101 - (self.autoPlay_speed + 30) * 2) / 100)
        self.episode_end.emit(total_reward, step, self.blockage_count)
        return episode

    def check_for_blockages(self, agent, valid_actions, pd_string):
        highest_action_str = " "
        all_actions = ['N', 'S', 'E', 'W']
        #print("checking for blocks")
        q_dicts = agent.return_q_dicts()
        current_state, has_item = agent.get_state()
        # Retrieve the Q-values for the current state
        highest_valued_action = -100
        for action in all_actions:
            action_q_value = q_dicts[pd_string].get((current_state, has_item, action))
            if not action_q_value:
                continue
            highest_valued_action = max( action_q_value, -100)
            if action_q_value == highest_valued_action:
                highest_action_str = action
        #print(highest_action_str)
        if highest_valued_action < -90:
            return

        #print(f"highest valued action {highest_valued_action}, {highest_action_str}")
        #print(f"valid actions: {valid_actions}")
        # Check if the highest valued action is in the valid actions
        if highest_action_str not in valid_actions:
            self.blockage_count += 1
            #print("blockage found")