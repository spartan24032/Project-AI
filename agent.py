# agent.py
class Agent:
    def __init__(self, actions, start_state, policy, learning_algorithm="Q-learning", alpha=0.5, gamma=0.5,
                 override_policy=None, override_max_step=0):
        self.Q_dicts = {}
        self.learning_algorithm = learning_algorithm
        self.alpha = alpha
        self.gamma = gamma
        self.actions = actions  # Possible actions
        self.state = start_state  # Agent's current state (position, has_item)
        self.reset_state = start_state
        self.loop1_data = {}

        self.default_policy = policy
        self.policy = policy  # Current policy in use
        self.override_policy = override_policy
        self.terminate_override_step = override_max_step

    def reset(self, pd_string):
        self.state = self.reset_state
        self.has_item = False
        if pd_string not in self.Q_dicts:
            self.Q_dicts[pd_string] = {}
    
    def get_state(self):
        return self.state, self.has_item

    def get_policy(self):
        return str(self.policy)[10:18]
    
    def update_state(self, new_state, has_item):
        self.state = new_state
        self.has_item = has_item

    def update_q_values(self, state, has_item, action, valid_actions, reward, next_state, next_has_item, pd_string, next_action):
        if pd_string not in self.Q_dicts:
            self.Q_dicts[pd_string] = {}

        if self.learning_algorithm == "Q-learning":
            current_q = self.Q_dicts[pd_string].get((state, has_item, action), 0)
            # Find the max Q-value for the NEXT state across all FUTURE possible actions
            q_values_next = [
                self.Q_dicts[pd_string].get((next_state, next_has_item, a))
                for a in valid_actions if (next_state, next_has_item, a) in self.Q_dicts[pd_string]
            ]
            next_max_q = max(q_values_next) if q_values_next else 0
            new_q = (current_q * (1 - self.alpha)) + self.alpha * (reward + self.gamma * next_max_q)

            self.Q_dicts[pd_string][(state, has_item, action)] = new_q

        if self.learning_algorithm == "SARSA":
            current_q = self.Q_dicts[pd_string].get((state, has_item, action), 0)
            # In SARSA, the action A' is chosen using the current policy from S' (it's passed into the function)
            next_q = self.Q_dicts[pd_string].get((next_state, next_has_item, next_action), 0)
            new_q = current_q + self.alpha * (reward + self.gamma * next_q - current_q)
            self.Q_dicts[pd_string][(state, has_item, action)] = new_q

    def choose_action(self, valid_actions, pd_string, step, episode, ep_based):
        if pd_string not in self.Q_dicts:
            self.Q_dicts[pd_string] = {}
        action = self.policy(self.state, self.has_item, self.Q_dicts[pd_string], valid_actions)
        if self.terminate_override_step != 0:
            if not ep_based:
                if self.override_policy and self.terminate_override_step > step:
                    action = self.override_policy(self.state, self.has_item, self.Q_dicts[pd_string], valid_actions)
                    if self.terminate_override_step <= step: # Revert to default policy if override duration has elapsed
                        self.policy = self.default_policy
            elif ep_based:
                if self.override_policy and self.terminate_override_step > episode:
                    action = self.override_policy(self.state, self.has_item, self.Q_dicts[pd_string], valid_actions)
                    if self.terminate_override_step <= episode:
                        self.policy = self.default_policy
        return action

    def return_q_dicts(self):
        return self.Q_dicts

    def store_loop1(self, idx, *args):
        self.loop1_data[idx] = args

    def get_loop1(self, idx):
        return self.loop1_data.get(idx)

    def display_q_values(self, pd_string):
        if pd_string == '5':
            print(f"  Q-values:")
        else:
            print(f"  Q-values (using complex state2, P/D states: {pd_string})")
        for action in self.actions:
            q_value = self.Q_dicts[pd_string].get((self.state, self.has_item, action))
            display_value = "--" if q_value is None else f"{q_value:.2f}"
            print(f"    {action}: {display_value}")

