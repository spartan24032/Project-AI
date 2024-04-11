# runSimulation.py
import time
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QTimer
import copy

class SimulationWorker(QObject):
    finished = pyqtSignal()
    # self.agents, env, episode, step, self.r
    update_display = pyqtSignal(object, object, int, int, int)
    # idx, agent_buffer, valid_actions_current, pd_string, action, reward
    update_qtable_display = pyqtSignal(int, object, list, str, str, int)
    requestPause = pyqtSignal()
    requestPlay = pyqtSignal(int)
    requestNext = pyqtSignal()
    requestSkip = pyqtSignal(int)

    def __init__(self, agents, env, complex_world2, episode_based, r, mskip):
        super().__init__()
        self.agents = agents
        self.env = env
        self.complex_world2 = complex_world2
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


        if self.episode_based:
            outer_loop = self.r
        else:
            outer_loop = 1

        for episode in range(outer_loop):
            self.env.reset()
            pd_string = self.env.generate_pd_string(self.complex_world2)
            for agent in self.agents:
                agent.reset(pd_string)

            # use verbose to control which episodes get output
            # [0, episodes - 1] to see the first and last.
            verbose = episode in [outer_loop - 1]

            if verbose:
                print(f"--- Episode {episode + 1} ---")
            if not self.episode_based:
                print(f"--- Running One Simulation with {self.r} total steps --- ")
            total_reward = 0
            step = 0
            while( (self.episode_based == False and step < self.r) or (self.episode_based == True and not self.env.dropoffs_complete()) ):
                if not self.episode_based:
                    verbose = step % 60 == 0

                if verbose:
                    print(f"\nStep {step}")
                    self.env.render(self.agents)
                pd_string = self.env.generate_pd_string(self.complex_world2)
                if self.skipTo is None:
                    agent_buffer = copy.deepcopy(self.agents)
                    environment_buffer = copy.deepcopy(self.env)
                    pd_buffer = copy.deepcopy(pd_string)
                    self.update_display.emit(agent_buffer, environment_buffer, episode, step, self.r)
                actions_taken = []

                for idx, agent in enumerate(self.agents):
                    if self.env.dropoffs_complete():
                        if verbose:
                            print(f"\nStep {step + 1}")
                            self.env.render(self.agents)
                            print(f"All dropoffs complete.\nTotal Reward for Episode {episode + 1}: {total_reward}\n")
                        break
                    if not self.episode_based and step > self.r or self.env.dropoffs_complete():
                        print("reached max steps OR completed all dropoffs, killing program")
                        exit()
                    old_state, old_has_item = agent.get_state()
                    # Get valid actions for the CURRENT state, before action is chosen
                    valid_actions_current = self.env.valid_actions(agent.get_state(), self.agents)
                    action = agent.choose_action(valid_actions_current, pd_string, step, episode, self.episode_based)
                    if verbose:
                        print(f"\033[91mAgent {idx}\033[0m {old_state}, Valid Actions: {valid_actions_current}")
                        self.agents[idx].display_q_values(pd_string)
                    reward = self.env.step(agent, action)  # Perform the action, moving to the new state
                    step += 1
                    # print(f"step {step}")
                    total_reward += reward
                    if verbose:
                        print(f"  selecting: {action}, Reward: {reward}")
                    if self.skipTo is None:
                        self.update_qtable_display.emit(idx, agent_buffer, valid_actions_current, pd_buffer, action, reward)
                    # Now, get valid actions for the NEW state, after action is performed
                    new_state, new_has_item = agent.get_state()  # This is effectively 'next_state' for Q-value update
                    valid_actions_next = self.env.valid_actions(agent.get_state(), self.agents)
                    # next_action is only for SARSA as it needs the future action based on policy
                    next_action = agent.choose_action(valid_actions_next, pd_string, step, episode, self.episode_based)
                    # Update Q-values using 'old_state' as current and 'new_state' as next
                    agent.update_q_values(old_state, old_has_item, action, valid_actions_next, reward, new_state,
                                          new_has_item, pd_string, next_action)

                    actions_taken.append((idx, action, reward, new_state, valid_actions_current))

                if not self.mskip:
                    if self.skipTo is not None:
                        if self.episode_based and episode > (int(self.skipTo) -1):
                            self.skipTo = None  # Reset skipping logic
                        elif not self.episode_based and step > (int(self.skipTo) - 1):
                            self.skipTo = None  # Reset skipping logic
                        continue
                    if self.paused:
                        while self.paused:
                            time.sleep(0.1)
                            if(self.moveOne > 0):
                                self.moveOne = self.moveOne - 1
                                break
                    if self.autoPlay:
                        time.sleep((101- (self.autoPlay_speed+30)*2) / 100)

        self.finished.emit()