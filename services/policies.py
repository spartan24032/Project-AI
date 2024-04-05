import random

def PRandom(agent_state, has_item, q_values, valid_actions):
    for action in ['pickup', 'dropoff']:
        if action in valid_actions:
            return action
    return random.choice(valid_actions)

def PExploit(agent_state, has_item, q_values, valid_actions):
    for action in ['pickup', 'dropoff']:
        if action in valid_actions:
            return action
    if random.random() < 0.80:
        max_q = max(q_values.get((agent_state, has_item, action), 0) for action in valid_actions)
        max_actions = [action for action in valid_actions if q_values.get((agent_state, has_item, action), 0) == max_q]
        return random.choice(max_actions)
    else:
        return random.choice(valid_actions)

def PGreedy(agent_state, has_item, q_values, valid_actions):
    for action in ['pickup', 'dropoff']:
        if action in valid_actions:
            return action
    max_q = max(q_values.get((agent_state, has_item, action), 0) for action in valid_actions)
    max_actions = [action for action in valid_actions if q_values.get((agent_state, has_item, action), 0) == max_q]
    return random.choice(max_actions)