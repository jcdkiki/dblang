from pymorphy3 import MorphAnalyzer
import os, sys
import re

morph_analyzer = MorphAnalyzer()

counter = 1

class Token:
    def __init__(self, s):
        self.word = s
        self.parses = morph_analyzer.parse(s)

        parsed = self.parses[0]
        self.normal_form = parsed.normal_form
        self.pos = parsed.tag.POS
        self.number = parsed.tag.number
        self.anim = parsed.tag.animacy
        self.gender = parsed.tag.gender
        self.case = parsed.tag.case
        self.tags = parsed.tag
            
    def __repr__(self):
        return f"{self.word}/{self.normal_form} {self.tags}"

    def node_str(self):
        return self.word
        
class Node:
    def __init__(self, val, children, terminal=False):
        global counter
        self.val = val
        self.children = children
        self.id = counter
        self.terminal = terminal
        counter += 1
    
    def __repr__(self):
        res = ""
        res += f'n{self.id} [label="{self.val}" shape=box style=filled fillcolor="{"#7fff7f" if self.terminal > 0 else "#ffff7f"}"]\n'
        for c in self.children:
            res += f'n{self.id} -> n{c.id}\n'
            res += repr(c)
        return res

tokens = []
cur_idx = -1
cur_token = None

def read_token():
    global cur_token, cur_idx

    node = Node("NONE", []) if cur_token is None else Node(cur_token.node_str(), [], True)
    
    cur_idx += 1
    cur_token = tokens[cur_idx]
    
    #print(f"READ OK {cur_token}")
    return node

def expect_keyword(word):
    if cur_token.word != word:
        raise Exception(f"Expected '{word}' keyword. Got {cur_token}")
    return read_token()

def is_keyword(word):
    return cur_token.word == word

def is_one_of_keywords(words):
    return cur_token.word in words

def expect_one_of_keywords(words):
    if not is_one_of_keywords(words):
        raise Exception(f"Expected one of '{words}' keywords. Got {cur_token}")
    return read_token()

def is_token(pos=None, number=None, anim=None, case=None, gender=None, tag=None):
    if pos is not None and cur_token.pos not in pos:
        return False
    if number is not None and cur_token.number not in number:
        return False
    if anim is not None and cur_token.anim not in anim:
        return False
    if case is not None and cur_token.case not in case:
        return False
    if gender is not None and cur_token.gender not in gender:
        return False
    if tag is not None and tag not in cur_token.tags:
        return False
    return True

def expect_token(pos=None, number=None, anim=None, case=None, gender=None, tag=None):
    if not is_token(pos, number, anim, case, gender, tag):
        raise Exception(f"Expected token pos={pos}, number={number}, anim={anim}, case={case}, tag={tag}. " \
                        f"Got {cur_token}")
    return read_token()

def is_number():
    return cur_token.word.isdigit()

def expect_number():
    if not cur_token.word.isdigit():
        raise Exception(f"Expected number, got {cur_token}")
    return read_token()

def expect_date():
    reg = r"^\d\d\.\d\d\.\d\d\d\d$"
    if not re.match(reg, cur_token.word):
        raise Exception(f"Expected date, got {cur_token}")
    return read_token()

### PARSE
def parse_query():
    t1 = parse_select_word()
    t2 = parse_what()
    if not is_keyword("EOF"):
        raise Exception(f"Expected EOF, got {cur_token}")
    return Node("query", [t1, t2])

def first_select_word(): return is_one_of_keywords(["выбери", "найди"])
def parse_select_word():
    return expect_one_of_keywords(["выбери", "найди"])
    
def first_what(): return is_keyword("граждан") or is_keyword("гражданина") or is_keyword("гражданку") or first_quantity()
def parse_what():
    if first_quantity() or is_keyword("граждан"):
        t1 = parse_quantity()
        t2 = expect_keyword("граждан")
        t3 = parse_optional_name("plur")
        return Node("what", [t1, t2, t3])
    if is_keyword("гражданина"):
        t1 = read_token()
        t2 = parse_optional_name("masc")
        return Node("what", [t1, t2])
    if is_keyword("гражданку"):
        t1 = read_token()
        t2 = parse_optional_name("femn")
        return Node("what", [t1, t2])
    raise Exception(f"Failed to match <what>. Got {cur_token}")

def parse_optional_name(gender):
    name = f"optional_name\n{gender}"
    if is_token(pos=["ADJF"]) or is_token(tag="Surn"):
        t1 = read_token()
        t2 = parse_optional_name1(gender)
        return Node(name, [t1, t2])
    if first_filters_citizen(gender, False):
        return Node(name, [parse_filters_citizen(gender, False)])
    return Node(name, [])
    
def parse_optional_name1(gender):
    name = f"optional_name1\n{gender}"
    if is_token(tag="Name"):
        t1 = read_token()
        t2 = expect_token(tag="Patr")
        t3 = parse_filters_citizen(gender, True)
        return Node(name, [t1, t2, t3])
    if first_filters_citizen(gender, True):
        return Node(name, [parse_filters_citizen(gender, True)])

def first_quantity(): return is_keyword("всех") or is_number()
def parse_quantity():
    if is_keyword("всех") or is_number():
        return Node("quantity", [read_token()])
    return Node("quantity", [])

def разыскиваемых(gender):
    match gender:
        case "femn": return "разыскиваемую"
        case "masc": return "разыскиваемого"
        case "plur": return "разыскиваемых"

def first_filters_citizen(gender, noname): return first_order() or first_filters_citizen1(gender, noname)
def parse_filters_citizen(gender, noname):
    name = f"filters_citizen\n{gender} {'noname' if noname else ''}"
    if first_order():
        t1 = parse_order()
        return Node(name, [t1])
    if first_filters_citizen1(gender, noname):
        return Node(name, [parse_filters_citizen1(gender, noname)])
    return Node(name, [])

def first_filters_citizen1(gender, noname):
    return is_one_of_keywords(["с", разыскиваемых(gender), "не", "возраста", "ростом"] + (["мужского", "женского"] if gender != "plur" else []))

def parse_filters_citizen1(gender, noname):
    name = f"filters_citizen1\n{gender} {'noname' if noname else ''}"
    if is_keyword("с"):
        t1 = read_token()
        t2 = parse_filters_citizen2(noname)
        t3 = parse_filters_citizen_next(gender, noname)
        return Node(name, [t1, t2, t3])
    if is_keyword(разыскиваемых(gender)):
        t1 = read_token()
        t2 = parse_filter_from()
        t3 = parse_filters_citizen_next(gender, noname)
        return Node(name, [t1, t2, t3])
    if is_keyword("не"):
        t1 = read_token()
        t2 = expect_keyword(разыскиваемых(gender))
        t3 = parse_filters_citizen_next(gender, noname)
        return Node(name, [t1, t2, t3])
    if is_keyword("возраста"):
        t1 = read_token()
        t2 = parse_number_filter()
        t3 = expect_keyword("лет")
        t4 = parse_filters_citizen_next(gender, noname)
        return Node(name, [t1, t2, t3, t4])
    if is_keyword("ростом"):
        t1 = read_token()
        t2 = parse_number_filter()
        t3 = expect_keyword("см")
        t4 = parse_filters_citizen_next(gender, noname)
        return Node(name, [t1, t2, t3, t4])
    if gender == "plur" and is_one_of_keywords(["мужского", "женского"]):
        t1 = read_token()
        t2 = expect_keyword("пола")
        t3 = parse_filters_citizen_next(gender, noname)
        return Node(name, [t1, t2, t3])
    raise Exception(f"Failed to match {name}. Got {cur_token}")

def first_filters_citizen2(noname): return is_one_of_keywords(["фамилией", "зарплатой"] + ([] if noname else ["именем"]))
def parse_filters_citizen2(noname):
    name = f"filters_citizen2\n{'noname' if noname else ''}"
    if not noname and is_keyword("именем"):
        t1 = read_token()
        t2 = expect_token(tag="Surn")
        t3 = expect_token(tag="Name")
        t4 = expect_token(tag="Patr")
        return Node(name, [t1, t2, t3, t4])
    if is_keyword("фамилией"):
        t1 = read_token()
        t2 = expect_token(tag="Surn")
        return Node(name, [t1, t2])
    if is_keyword("зарплатой"):
        t1 = read_token()
        t2 = parse_number_filter()
        return Node(name, [t1, t2])
    raise Exception(f"Failed to match {name}. Got {cur_token}")

def first_filters_citizen_next(gender, noname): return is_one_of_keywords(",", "в")
def parse_filters_citizen_next(gender, noname):
    name = f"filters_citizen_next\n{gender} {'noname' if noname else ''}"
    if is_keyword(","):
        t1 = read_token()
        t2 = parse_filters_citizen1(gender, noname)
        return Node(name, [t1, t2])
    if is_keyword("в"):
        return Node(name, [parse_order()])
    return Node(name, [])

def first_filter_from(): return is_keyword("с")
def parse_filter_from():
    if is_keyword("с"):
        t1 = read_token()
        t2 = expect_date()
        return Node("filter_from", [t1, t2])
    return Node("filter_from", [])

def first_number_filter(): return is_one_of_keywords(["больше", "меньше", "более", "менее", "не", "от"]) or is_number()
def parse_number_filter():
    if is_one_of_keywords(["больше", "меньше", "более", "менее"]):
        t1 = read_token()
        t2 = expect_number()
        return Node("number_filter", [t1, t2])
    if is_keyword("не"):
        t1 = read_token()
        t2 = parse_more_less()
        t3 = expect_number()
        return Node("number_filter", [t1, t2, t3])
    if is_keyword("от"):
        t1 = read_token()
        t2 = expect_number()
        t3 = expect_keyword("до")
        t4 = expect_number()
        return Node("number_filter", [t1, t2, t3, t4])
    if is_number():
        t1 = read_token()
        return Node("number_filter", [t1])
    raise Exception(f"Failed to match number_filter. Got {cur_token}")

def parse_more_less():
    return Node("more_less", expect_one_of_keywords(["больше", "меньше"]))

def first_order_tail(): return is_keyword(",")
def parse_order_tail():
    if is_keyword(","):
        t1 = read_token()
        t2 = parse_asc_desc()
        t3 = expect_token(pos=['NOUN'], number=['sing'], case=['gent'])
        t4 = parse_order_tail()
        return Node("order_tail", [t1, t2, t3, t4])
    return Node("order_tail", [])

def first_order(): return is_keyword("в")
def parse_order():
    if is_keyword("в"):
        t1 = expect_keyword("в")
        t2 = expect_keyword("порядке")
        t3 = parse_asc_desc()
        t4 = expect_token(pos=['NOUN'], number=['sing'], case=['gent'])
        t5 = parse_order_tail()
        return Node("order", [t1, t2, t3, t4, t5])
    return Node("order", []) # eps

def first_asc_desc(): return is_one_of_keywords(["возрастания", "увеличения", "убывания", "уменьшения"])
def parse_asc_desc():
    return Node("asc_desc", [expect_one_of_keywords(["возрастания", "увеличения", "убывания", "уменьшения"])])

if len(sys.argv) != 2:
    print("Usage: python3 main.py <output_file>")
    exit(1)

ss = input().split()
tokens = [ Token(s) for s in ss ] + [ Token("EOF") ]
read_token()

try:
    ast = parse_query()
except Exception as e:
    print(*ss)
    for i, s in enumerate(ss):
        if i == cur_idx:
            print("^"*len(s), end=' ')
            break
        else:
            print(" "*len(s), end=' ')
    print(e)
    exit(1)

open("result.dot", "w").write("digraph {\n" + str(ast) + "}\n")
os.system(f"dot -Tpng result.dot > {sys.argv[1]}")