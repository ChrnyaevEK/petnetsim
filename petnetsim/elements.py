import random as _random
from copy import deepcopy

_default_context_init = {
    'counters': {'P': 1, 'T': 1, 'A': 1, 'I': 1}
}

_default_context = deepcopy(_default_context_init)


def default_context():
    return _default_context


def new_context():
    return deepcopy(_default_context_init)


def reset_default_context():
    # preserve _default_context as same object, but deepcopy all included
    _default_context.clear()
    _default_context.update({k: deepcopy(v) for k, v in _default_context_init.items()})


class Place:
    INF_CAPACITY = 0

    def __init__(self, name=None, init_tokens=0, capacity=INF_CAPACITY, context=_default_context):
        if name is None:
            self.name = '_P_'+str(context['counters']['P'])
            context['counters']['P'] += 1
        else:
            self.name = name
        self.capacity = capacity
        self.init_tokens = init_tokens
        self.tokens = init_tokens

    def can_add(self, n_tokens):
        return self.capacity == Place.INF_CAPACITY or self.tokens + n_tokens <= self.capacity

    def can_remove(self, n_tokens):
        return self.tokens - n_tokens >= 0

    def add(self, n_tokens):
        self.tokens += n_tokens

    def remove(self, n_tokens):
        self.tokens -= n_tokens

    def reset(self):
        self.tokens = self.init_tokens


class Transition:
    def __init__(self, name, context=_default_context):
        if name is None:
            self.name = '_T_'+str(context['counters']['T'])
            context['counters']['T'] += 1
        else:
            self.name = name
        self.inputs = set()   # Arc, Inhibitor
        self.outputs = set()  # Arc, Inhibitor
        self.fired_times = 0
        self.in_arcs = []  # init in reset
        self.inhibitors = []  # init in reset

    def enabled(self):
        # if len(self.inhibitors):
        #     print(self.name, 'inhibitors (name, state):',
        #           [(inhibitor.name, inhibitor.source.can_remove(inhibitor.n_tokens))
        #            for inhibitor in self.inhibitors])

        return all(arc.source.can_remove(arc.n_tokens) for arc in self.in_arcs) \
               and all(arc.target.can_add(arc.n_tokens) for arc in self.outputs) \
               and not any(inhibitor.source.can_remove(inhibitor.n_tokens) for inhibitor in self.inhibitors)

    def fire(self):
        for arc in self.in_arcs:
            arc.source.remove(arc.n_tokens)

        for arc in self.outputs:
            arc.target.add(arc.n_tokens)

        self.fired_times += 1

    def freeze(self):
        self.inputs = frozenset(self.inputs)
        self.outputs = frozenset(self.outputs)
        self.in_arcs = tuple(arc for arc in self.inputs if isinstance(arc, Arc))
        self.inhibitors = tuple(inhibitor for inhibitor in self.inputs if isinstance(inhibitor, Inhibitor))
        # note: inhibitors can't be outputs

    def reset(self):
        self.fired_times = 0


class TransitionPriority(Transition):
    def __init__(self, name, priority, context=_default_context):
        super().__init__(name, context)
        self.priority = priority


def constant_distribution(t_min, t_max):
    return t_min


def uniform_distribution(t_min, t_max):
    return _random.uniform(t_min, t_max)


class TransitionTimed(Transition):
    T_EPSILON = 1e6

    def __init__(self, name, t_min, t_max=1, p_distribution_func=constant_distribution, context=_default_context):
        super().__init__(name, context)
        self.remaining = 0
        self.t_min = t_min
        self.t_max = t_max
        self.p_distribution_func = p_distribution_func
        self.is_waiting = False
        self.time = 0.0

    def enabled(self):
        return super().enabled() and not self.is_waiting

    def fire(self):
        super().fire()
        self.is_waiting = False

    def wait(self):
        self.is_waiting = True
        self.time = self.p_distribution_func(self.t_min, self.t_max)
        return self.time

    def reset(self):
        super().reset()
        self.is_waiting = False


class TransitionStochastic(Transition):
    # NOTE: stochastic is almost normal transition
    def __init__(self, name, probability, context=_default_context):
        super().__init__(name, context)
        self.probability = probability


class Arc:
    def __init__(self, source, target, n_tokens=1, name=None, context=_default_context):
        if name is None:
            self.name = '_Arc_'+str(context['counters']['A'])
            context['counters']['A'] += 1
        else:
            self.name = name
        self.source = source
        self.target = target
        self.n_tokens = n_tokens

        if not (isinstance(self.source, str) or isinstance(self.target, str)):
            self.connect(None)

    def connect(self, names_lookup):
        if isinstance(self.source, str):
            self.source = names_lookup[self.source]
        if isinstance(self.target, str):
            self.target = names_lookup[self.target]

        if isinstance(self.source, Transition):
            if not isinstance(self.target, Place):
                raise RuntimeError('arc from Transition must go to a Place')
            self.source.outputs.add(self)
        if isinstance(self.target, Transition):
            if not isinstance(self.source, Place):
                raise RuntimeError('arc to Transition must go from a Place')
            self.target.inputs.add(self)

    @property
    def target_infinite_capacity(self):
        if not isinstance(self.target, Place):
            raise RuntimeError('target_is_infinite can be asked only if target is a Place')
        return self.target.capacity == Place.INF_CAPACITY


class Inhibitor:
    def __init__(self, source, target, n_tokens=1, name=None, context=_default_context):
        if name is None:
            self.name = '_Inhibitor_'+str(context['counters']['I'])
            context['counters']['I'] += 1
        else:
            self.name = name
        self.source = source
        self.target = target
        self.n_tokens = n_tokens

        if not (isinstance(self.source, str) or isinstance(self.target, str)):
            self.connect(None)

    def connect(self, names_lookup):
        if isinstance(self.source, str):
            self.source = names_lookup[self.source]
        if isinstance(self.target, str):
            self.target = names_lookup[self.target]

        if not isinstance(self.source, Place):
            raise RuntimeError('inhibitor source must be a Place')

        if isinstance(self.target, Transition):
            self.target.inputs.add(self)
        else:
            raise RuntimeError('inhibitor target must be a Transition')

