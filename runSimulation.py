# runSimulation.py
import time
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QTimer
import copy
import pandas as pd 
import matplotlib.pyplot as plt
import numpy as np


class SimulationWorker(QObject):
    finished = pyqtSignal()
    # self.agents, env, episode, step, self.r, episode_based, totalsteps
    update_display = pyqtSignal(object, object, int, int, int, bool, int)
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
        self.totalsteps = 0
    def print_excel(self):
            excel_writer = pd.ExcelWriter('Q_EXP3_Complex_SEED_2_Alpha_0.45_PRANDOM_500_PEXPLOIT_8500.xlsx', engine='xlsxwriter')

            for num, agent in enumerate(self.agents):
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
    def coordination(self):
        agent_data ={}
        for num,agent in enumerate(self.agents):
            #print(f"Agent {num}")
            agent_data[num] = {}
            for agent_blocking in agent.blocked_by.keys():
                #print(agent_blocking)
                sorted_p_d = (sorted(agent.blocked_by[agent_blocking],key = lambda x:x[0]))
                #rint(sorted(sorted_p_d,key= lambda x: x[1]))
                agent_data[num][agent_blocking]=(sorted(sorted_p_d,key= lambda x: x[1]))
        print(agent_data)

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
        print('here')
        self.print_excel()
        self.coordination()
        self.finished.emit()

    def core_logic(self, episode):
        episode += 1
        self.env.reset()
        pd_string = self.env.generate_pd_string(self.complex_world2)
        for agent in self.agents:
            agent.reset(pd_string)

        # use verbose to control which episodes get output
        # [0, self.r - 1] to see the first and last.
        verbose =  False #episode in [self.r - 1]

        if verbose:
            print(f"--- Episode {episode + 1} ---")

        total_reward = 0
        step = 0
        while (not self.env.dropoffs_complete()):
            if not self.episode_based:
                verbose = False# step % 1000 == 0
                if self.totalsteps > self.r:
                    return episode

            if verbose:
                print(f"\nStep {step}")
                self.env.render(self.agents)
            pd_string = self.env.generate_pd_string(self.complex_world2)
            if self.skipTo is None:
                agent_buffer = copy.deepcopy(self.agents)
                environment_buffer = copy.deepcopy(self.env)
                pd_buffer = copy.deepcopy(pd_string)
                self.update_display.emit(
                    agent_buffer, environment_buffer, episode, step, self.r, self.episode_based, self.totalsteps
                )
            actions_taken = []

            for idx, agent in enumerate(self.agents):
                if verbose:
                    print(f"\nStep {step + 1}")
                    self.env.render(self.agents)
                    print(f"All dropoffs complete.\nTotal Reward for Episode {episode + 1}: {total_reward}\n")
                old_state, old_has_item = agent.get_state()
                # Get valid actions for the CURRENT state, before action is chosen
                valid_actions_current = self.env.valid_actions(agent.get_state(), self.agents)
                self.env.blocked_actions(agent.get_state(), self.agents,agent)
                action = agent.choose_action(valid_actions_current, pd_string, step, episode, self.episode_based)
                if verbose:
                    print(f"\033[91mAgent {idx}\033[0m {old_state}, Valid Actions: {valid_actions_current}")
                    self.agents[idx].display_q_values(pd_string)
                reward = self.env.step(agent, action)  # Perform the action, moving to the new state
                step += 1
                self.totalsteps += 1
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
            #time.sleep(1)
        return episode