from functools import lru_cache
from base import *

def query():
    return add_rule('<query>', [
        [select_word(), what()]
    ])

def select_word():
    return add_rule('<word>', [
        ['выбери'],
        ['найди']
    ])

def what():
    return add_rule('<what>', [
        [quantity(), 'граждан', filters_citizen('plural', [])],
        ['гражданина', optional_name('masc', ['gender'])],
        ['гражданку', optional_name('femn', ['gender'])]
    ])

def optional_name(gender, forbid):
    return add_rule(f'<optional_name_{gender}{forbid_str(forbid)}>', [
        ['<surn>', optional_name_tail(gender, forbid)],
        [filters_citizen(gender, forbid)]
    ])

def optional_name_tail(gender, forbid):
    return add_rule(f'<optional_name_tail_{gender}>', [
        ['<name>', '<patr>', filters_citizen(gender, forbid + ['name'])],
        [filters_citizen(gender, forbid + ['name'])],
    ])

def quantity():
    return add_rule('<quantity>', [
        ['<number>'],
        ['всех'],
        []
    ])

def filters_citizen(gender, forbid):
    res = [
        [order()],
        []
    ]

    if len(forbid) != TOTAL_CITIZEN_TRAITS:
        res.append([filters_citizen1(gender, forbid)])     
    
    return add_rule(f'<filters_citizen_{gender}{forbid_str(forbid)}>', res)

def разыскиваемых(gender):
    match gender:
        case 'masc': return 'разыскиваемого'
        case 'femn': return 'разыскиваемую'
        case 'plural': return 'разыскиваемых'

def судимых(gender):
    match gender:
        case 'masc': return 'судимого'
        case 'femn': return 'судимую'
        case 'plural': return 'судимых'

def filters_citizen1(gender, forbid):
    name = f'<filters_citizen1_{gender}{forbid_str(forbid)}>'
    if name in grammar: return name

    res = []
    _next = filters_citizen_next

    if 'name' not in forbid or 'wage' not in forbid:
        res.append(['с', filters_citizen2(gender, forbid)])

    if 'wanted' not in forbid or 'convicted' not in forbid:
        res.append(['не', filters_citizen_not(gender, forbid)])

    if 'wanted' not in forbid:
        res.append([разыскиваемых(gender), filter_from(), _next(gender, forbid + ['wanted'])])

    if 'convicted' not in forbid:
        res.append([судимых(gender), _next(gender, forbid + ['convicted'])])

    if 'gender' not in forbid:
        res.append(['женского', 'пола', _next(gender, forbid + ['gender'])])
        res.append(['мужского', 'пола', _next(gender, forbid + ['gender'])])
    
    if 'age' not in forbid:
        res.append(['возраста', number_filter(), 'лет', _next(gender, forbid + ['age'])])
    
    if 'height' not in forbid:
        res.append(['ростом', number_filter(), 'см', _next(gender, forbid + ['height'])])

    return add_rule(name, res)

def filters_citizen_not(gender, forbid):
    name = f'<filters_citizen_not_{gender}{forbid_str(forbid)}>'
    if name in grammar: return name

    res = []
    _next = filters_citizen_next

    if 'wanted' not in forbid:
        res.append([разыскиваемых(gender), filter_from(), _next(gender, forbid + ['wanted'])])

    if 'convicted' not in forbid:
        res.append([судимых(gender), _next(gender, forbid + ['convicted'])])

    return add_rule(name, res)


def filters_citizen2(gender, forbid):
    name = f'<filters_citizen2_{gender}{forbid_str(forbid)}>'
    if name in grammar: return name

    res = []
    _next = filters_citizen_next

    if 'name' not in forbid:
        res.append(['именем', '<surn>', '<name>', '<patr>', _next(gender, forbid + ['name'])])
        res.append(['фамилией', '<surn>', _next(gender, forbid + ['name'])])
    
    if 'wage' not in forbid:
        res.append(['зарплатой', number_filter(), _next(gender, forbid + ['wage'])])

    return add_rule(name, res)

def filters_citizen_next(gender, forbid):
    name = f'<filters_citizen_next_{gender}{forbid_str(forbid)}>'
    if name in grammar: return name
    
    res = [
        [order()],
        []
    ]

    if len(forbid) != TOTAL_CITIZEN_TRAITS:
        res.append([ ",", filters_citizen1(gender, forbid)])

    return add_rule(name, res)

def number_filter():
    return add_rule('<number_filter>', [
        ['<number>'],
        ['больше', '<number>'],
        ['меньше', '<number>'],
        ['не', 'больше', '<number>'],
        ['от', '<number>', 'до', '<number>']
    ])

def order():
    return add_rule('<order>', [
        ['в', 'порядке', asc_desc(), order_tail2([])]
    ])

def asc_desc():
    return add_rule('<asc_desc>', [
        ['возрастания'],
        ['убывания']
    ])

def order_tail(forbid = []):
    name = f'<order_tail{forbid_str(forbid)}>'
    if name in grammar: return name

    res = [ [] ]

    if len(forbid) != 4:
        res.append([",", asc_desc(), order_tail2(forbid)])

    return add_rule(name, res)

def order_tail2(forbid):
    name = f'<order_tail2{forbid_str(forbid)}>'
    if name in grammar: return name

    res = [ [] ]

    if 'name'   not in forbid: res.append(["имени",    order_tail(forbid + ['name'])])
    if 'wage'   not in forbid: res.append(["зарплаты", order_tail(forbid + ['wage'])])
    if 'age'    not in forbid: res.append(["возраста", order_tail(forbid + ['age'])])
    if 'height' not in forbid: res.append(["роста",    order_tail(forbid + ['height'])])

    return add_rule(name, res)    

def filter_from():
    return add_rule('<filter_from>', [
        ['с', '<date>'],
        []
    ])

query()

for name, rules in grammar.items():
    print(name, "::=")
    for i in range(0, len(rules)):
        rule = rules[i]
        if len(rule) == 0:
            print("    <eps>", "|" if i != len(rules) - 1 else "")
        else:
            print("   ", *rule, "|" if i != len(rules) - 1 else "")
    print()