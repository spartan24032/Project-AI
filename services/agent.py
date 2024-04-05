# agent.py

class Agent:
    def __init__(self, actions, start_state, policy, alpha=0.5, gamma=0.5):
        self.Q_dicts = {}
        self.alpha = alpha
        self.gamma = gamma
        self.actions = actions  # Possible actions
        self.state = start_state  # Agent's current state (position, has_item)
        self.reset_state = start_state
        self.policy = policy

    def reset(self, pd_string):
        self.state = self.reset_state
        self.has_item = False
        if pd_string not in self.Q_dicts:
            self.Q_dicts[pd_string] = {}
    
    def get_state(self):
        return self.state, self.has_item
    
    def update_state(self, new_state, has_item):
        self.state = new_state
        self.has_item = has_item

    def update_q_values(self, state, has_item, action, valid_actions, reward, next_state, next_has_item, pd_string):
        if pd_string not in self.Q_dicts:
            self.Q_dicts[pd_string] = {}

        current_q = self.Q_dicts[pd_string].get((state, has_item, action))
        # Find the max Q-value for the NEXT state across all FUTURE possible actions
        q_values_next = [
            self.Q_dicts[pd_string].get((next_state, next_has_item, a))
            for a in valid_actions if (next_state, next_has_item, a) in self.Q_dicts[pd_string]
        ]
        next_max_q = max(q_values_next) if q_values_next else -1.0

        if current_q is None:
            new_q = reward
        else:
            new_q = current_q + self.alpha * (reward + self.gamma * next_max_q - current_q)
        self.Q_dicts[pd_string][(state, has_item, action)] = new_q


    def choose_action(self, valid_actions, pd_string):
        return self.policy(self.state, self.has_item, self.Q_dicts[pd_string], valid_actions)

    def display_q_values(self, pd_string):
        if pd_string == 5:
            print(f"  Q-values:")
        else:
            print(f"  Q-values (using complex state2, P/D states: {pd_string})")
        for action in self.actions:
            q_value = self.Q_dicts[pd_string].get((self.state, self.has_item, action))
            display_value = "--" if q_value is None else f"{q_value:.2f}"
            print(f"    {action}: {display_value}")
