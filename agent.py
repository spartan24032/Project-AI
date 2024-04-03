# agent.py
import random

class Agent:
    def __init__(self, actions, start_state, policy, alpha=0.5, gamma=0.5):
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

    def update_q_values(self, state, has_item, action, valid_actions, reward, next_state, next_has_item):
        # Assemble the current state and action into a tuple
        current_q = self.Q.get((state, has_item, action))
        # Find the max Q-value for the NEXT state across all FUTURE possible actions
        q_values_next = [self.Q.get((next_state, next_has_item, a)) for a in valid_actions if (next_state, next_has_item, a) in self.Q]
        next_max_q = max(q_values_next) if q_values_next else -1.0

        if current_q is None:
            new_q = reward  # or some initialization logic
        else:
            new_q = current_q + self.alpha * (reward + self.gamma * next_max_q - current_q)
        self.Q[(state, has_item, action)] = new_q


    def choose_action(self, valid_actions):
        return self.policy(self.state, self.has_item, self.Q, valid_actions)

    def display_q_values(self):
        print("  Q-values:")
        for action in self.actions:
            q_value = self.Q.get((self.state, self.has_item, action))
            display_value = "--" if q_value is None else f"{q_value:.2f}"
            print(f"    {action}: {display_value}")

