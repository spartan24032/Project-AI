# agent.py
import random

class Agent:
    def __init__(self, actions, start_state, policy, alpha=0.1, gamma=0.9):
        self.Q = {}  # Initialize Q-values dictionary
        self.alpha = alpha  # Learning rate
        self.gamma = gamma  # Discount factor
        self.actions = actions  # Possible actions
        self.state = start_state  # Agent's current state (position and has_item flag)
        self.reset_state = start_state
        self.policy = policy

    def reset(self):
        self.state = self.reset_state
        self.has_item = False
    
    def get_state(self):
        return self.state, self.has_item
    
    def update_state(self, new_state, has_item):
        self.state = new_state
        self.has_item = has_item

    def update_q_values(self, state, has_item, action, reward, next_state, next_has_item):
        # Assemble the current state and action into a tuple
        current_q = self.Q.get((state, has_item, action), 0.0)
        # Find the max Q-value for the next state across all possible actions
        next_max_q = max([self.Q.get((next_state, next_has_item, a), 0.0) for a in self.actions])
        # Calculate the new Q-value using the Q-learning formula
        new_q = current_q + self.alpha * (reward + self.gamma * next_max_q - current_q)
        # Update the Q-value for the current state and action
        self.Q[(state, has_item, action)] = new_q

    def choose_action(self, valid_actions):
        return self.policy(self.state, self.has_item, self.Q, valid_actions)

    def display_q_values(self):
        print("Current Q-values:")
        for action in self.actions:
            print(f"  {action}: {self.Q.get((self.state, self.has_item, action), 0.0):.2f}")
        print()
