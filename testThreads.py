import threading
import time
from Other import ns, simulation_thread

class SimControl:
    def __init__(self):
        self.next_step_event = threading.Event()



if __name__ == "__main__":
    sim_control = SimControl()
    t = threading.Thread(target=simulation_thread, args=(sim_control,))
    t.start()
    time.sleep(5)
    ns(sim_control)


