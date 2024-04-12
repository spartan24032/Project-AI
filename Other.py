import time

def ns(sim_cont):
    # Simulate clicking "Next" after some time
    print("Next clicked, setting next_step_event")
    sim_cont.next_step_event.set()

def simulation_thread(sim_control):
    while True:  # Simplified loop for testing
        print("waiting on signal")
        sim_control.next_step_event.wait()
        print("signal reached thread")
        sim_control.next_step_event.clear()
        # Simulate doing some work
        time.sleep(1)