from itertools import count, combinations
from petnetsim import *
import numpy as np


def run():
    C = Place('C')
    D = Place('D')

    places = [Place('A', init_tokens=2), Place('B', init_tokens=5), C, D]

    T2 = Transition('T2')
    transitions = [Transition('T1'), T2]

    # arcs can be constructed with names which will be replaced by objects by PetriNet object
    arcs = [Arc('A', 'T1', 1),
            Inhibitor('B', 'T1', 1),
            Arc('T1', C, 1),
            Arc('B', T2, 1),
            Arc(T2, D, 1),
            ]

    petri_net = PetriNet(places, transitions, arcs)

    print('------------------------------------')
    print(' run')


    petri_net.reset()

    max_steps = 100

    petri_net.print_places()

    while not petri_net.ended and petri_net.step_num < max_steps:
        print('--------------- step', petri_net.step_num)
        petri_net.step()
        petri_net.print_places()

    if petri_net.ended:
        print('  breaking condition')
    else:
        print('  max steps reached')

    print('transitions stats')
    for t in transitions:
        print(t.name, t.fired_times, sep=': ')


run()
