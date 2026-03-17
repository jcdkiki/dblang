from collections import defaultdict

TERMINALS = ['<surn>', '<name>', '<path>', '<number>', '<date>']
TOTAL_CITIZEN_TRAITS = 7

def forbid_str(forbid):
    f = sorted(forbid)
    return "" if len(f) == 0 else "_" + "_".join([ "no" + x for x in f])

def can_be_empty(rule):
    for x in rule:
        if len(x) == 0: return True
    return False

def is_terminal(token):
    return (token in TERMINALS) or not (token[0] == '<')

def compute_first_of_sequence(seq):
    result = set()
    for sym in seq:
        if is_terminal(sym):
            result.add(sym)
            return result
        else:
            result |= first[sym]
            if not can_be_empty(grammar[sym]):
                return result
    return result

def add_rule(name, rule):
    global grammar
    grammar[name] = rule
    
    F = set()
    for seq in rule:
        seq_F = compute_first_of_sequence(seq)
        assert len(F.intersection(seq_F)) == 0
        F |= seq_F

    first[name] = F
    return name

grammar       = {}
first         = {}
follow = defaultdict(set)