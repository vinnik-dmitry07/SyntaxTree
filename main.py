from lark import Lark
from lark.tree import Tree
from lark.lexer import Token
from PIL import Image
import sys
import os.path
import shutil

oper = {
    'less': '<',
    'leq': '<=',
    'eq': '=',
    'neq': '!=',
    'gr': '>',
    'gre': '>=',
    'add': '+',
    'sub': '-',
    'mult': '*',
    'div': '/',
    'mod': '%',
}

tokens = {
    'assign': ":=",
    'semi': ';',
    'lb': '(',
    'rb': ')',
}
tokens.update(oper)


def superscript(char):
    superscripts = {
        'A': 'ᴬ',
        'B': 'ᴮ',
        'D': 'ᴰ',
        'E': 'ᴱ',
        'G': 'ᴳ',
        'H': 'ᴴ',
        'I': 'ᴵ',
        'J': 'ᴶ',
        'K': 'ᴷ',
        'L': 'ᴸ',
        'M': 'ᴹ',
        'N': 'ᴺ',
        'O': 'ᴼ',
        'P': 'ᴾ',
        'R': 'ᴿ',
        'T': 'ᵀ',
        'U': 'ᵁ',
        'V': 'ⱽ',
        'W': 'ᵂ',
        '2': '²',
    }
    return superscripts[char] if char in superscripts.keys() else '^' + char


def overline(s):
    return s.replace("", '̅')[:-1]


def pydot__tree_to_png(tree_, filename, rankdir="LR", **kwargs):
    import pydot
    graph = pydot.Dot(graph_type='digraph', rankdir=rankdir, **kwargs)

    i = [0]

    def new_leaf(leaf):
        node = pydot.Node(i[0], label=str(leaf))
        i[0] += 1
        graph.add_node(node)
        return node

    def _to_pydot(subtree):
        color = hash(subtree.data) & 0xffffff
        color |= 0x808080

        subnodes = [_to_pydot(child) if isinstance(child, Tree) else new_leaf(child)
                    for child in subtree.children]
        node = pydot.Node(i[0], style="filled", fillcolor="#%x" % color,
                          label=(r'\<{}\>' if subnodes else '{}').
                          format(subtree.data if subtree.data not in tokens.keys() else tokens[subtree.data]))
        i[0] += 1
        graph.add_node(node)

        for subnode in subnodes:
            graph.add_edge(pydot.Edge(node, subnode))

        return node

    _to_pydot(tree_)
    graph.write_png(filename)


parser = Lark(
    '''
    begin: "begin"
    end: "end"
    assign: ":="
    semi: ";"
    if: "if"
    then: "then"
    else: "else"
    while: "while"
    do: "do"
    skip: "skip"
    add: "+"
    sub: "-"
    mult: "*"
    div: "/"
    mod: "%"
    lb: "("
    rb: ")"
    less: "<"
    leq: "<="
    eq: "="
    neq: "!="
    gr: ">"
    gre: ">="
    or: "or"
    and: "and"
    not: "not"
    
    programa: begin operator end
    
    operator: zmina assign vyraz
            | operator semi operator
            | if umova then operator [else operator]
            | while umova do operator
            | begin operator end
            | skip
    
    vyraz: chyslo
         | zmina
         | vyraz add vyraz
         | vyraz sub vyraz
         | vyraz mult vyraz
         | vyraz div vyraz
         | vyraz mod vyraz
         | lb vyraz rb
    
    umova: "true" -> true
         | "false" -> false
         | vyraz less vyraz
         | vyraz leq vyraz
         | vyraz eq vyraz
         | vyraz neq vyraz
         | vyraz gr vyraz
         | vyraz gre vyraz
         | umova or umova
         | umova and umova
         | not umova
         | lb umova rb
    
    zmina: ("A".."Z")
    chyslo: ("0".."9")+
    WHITESPACE: (" " | "\\n")+
    %ignore WHITESPACE
    ''',
    start='programa')

tasks = {
    'GCD':
        '''
        begin
        while M != N do
            if M > N then
                M := M - N
            else
                N := N - M
        end
        ''',
    'A plus B to R':
        '''
        begin
            R := A;
            I := 0;
            while I < B do
            begin
                R := R + 1;
                I := I + 1
            end
        end
        ''',
    'A mul B to R':
        '''
        begin
            if B < 0 then
            begin
                A := 0 - A;
                B := 0 - B
            end;
            R := 0;
            while B > 0 do
            begin
                R := R + A;
                B := B - 1
            end
        end
        ''',
    'A div B to Q, A mod B to R':
        '''
        begin
            Q := 0;
            R := A;
            while R >= D do
            begin
                Q := Q + 1;
                R := R - D
            end
        end
        ''',
    'N! to R':
        '''
        begin
            if N < 0 then
                R := 0
            else
            begin
                R := 1;
                while N > 1 do
                begin
                    R := R * N;
                    N := N - 1
                end
            end
        end
        ''',
    'A pow B to R':
        '''
            begin
                R := 1;
                while B > 0 do
                begin
                    P := 0;
                    while R > 0 do
                    begin
                        P := P + A;
                        R := R - 1
                    end;
                    R := P;
                    B := B - 1
                end
            end
        ''',
    'floor(logX(Y))':
        '''
        begin
            R := 0;
            M := 0;
            while Y > 1 do
            begin
                R := R + 1;
                Y := Y / X;
                M := Y % X
            end;
            if M > 0 then
                R := R - 1
        end
        ''',
}


def to_str(tree_):
    s = ''
    for x in tree_.iter_subtrees():
        if len(x.children) == 0:
            s += (x.data if x.data not in tokens.keys() else tokens[x.data]) + ' '
        elif len(x.children) == 1 and type(x.children[0]) == Token:
            s += x.children[0] + ' '
    return s.strip()


class Sem:
    def __init__(self, type_, tree_):
        self.type = type_
        self.tree = tree_

    def __str__(self):
        return 'Sem_' + self.type + '(' + to_str(self.tree) + ')'


def insert_position(position, list1, list2):
    return list1[:position] + list2 + list1[position:]


def traverse(lst):
    for s in lst:
        f.write(str(s))
    f.write('\n')

    n = a = None
    for n, a in enumerate(lst):
        if type(a) == Sem:
            break
    if type(a) == str:
        return

    subtree = a.tree
    if len(subtree.children) == 1:
        if subtree.children[0].data == 'zmina':
            lst[n] = subtree.children[0].children[0] + '=>'
            traverse(lst)
        elif subtree.children[0].data == 'chyslo':
            lst[n] = overline(subtree.children[0].children[0])
            traverse(lst)

    elif subtree.data == 'programa':
        lst[n] = Sem('S', subtree.children[1])
        traverse(lst)

    elif len(subtree.children) >= 4:
        if subtree.children[0].data == 'if':

            lst = insert_position(n, lst,
                                  ['IF(', Sem('B', subtree.children[1]), ', ', Sem('S', subtree.children[3]), ', ',
                                   Sem('S', subtree.children[5]) if len(subtree.children) == 6 and
                                                                    subtree.children[4].data == 'else' else 'id',
                                   ')'])
            lst.remove(a)
            traverse(lst)
        elif subtree.children[0].data == 'while':
            lst = insert_position(n, lst,
                                  ['WH(', Sem('B', subtree.children[1]), ', ', Sem('S', subtree.children[3]), ')'])
            lst.remove(a)
            traverse(lst)
    elif len(subtree.children) == 3:
        if subtree.children[0].data == 'begin':
            lst[n] = Sem('S', subtree.children[1])
            traverse(lst)

        sign = subtree.children[1].data
        if sign == 'assign':
            x = to_str(subtree.children[0])
            lst = insert_position(n, lst, [f'AS{superscript(x)}(', Sem('A', subtree.children[2]), ')'])
            lst.remove(a)
            traverse(lst)
        elif sign == 'semi':
            lst = insert_position(n, lst, [Sem('S', subtree.children[0]), ' • ', Sem('S', subtree.children[2])])
            lst.remove(a)
            traverse(lst)
        elif sign in oper.keys():
            # sign = oper[sign]
            lst = insert_position(n, lst,
                                  [f'S{superscript("2")}({sign}, ',
                                   Sem('A', subtree.children[0]), ', ',
                                   Sem('A', subtree.children[2]), ')'])
            lst.remove(a)
            traverse(lst)
    return lst


for task_name, task_text in tasks.items():
    if os.path.exists(task_name):
        shutil.rmtree(task_name)
    os.mkdir(task_name)

    f = open(os.path.join(task_name, 'semantic_term.txt'), 'w', encoding="utf-8")
    tree = parser.parse(task_text)

    traverse([Sem('P', tree)])
    f.close()

    pydot__tree_to_png(tree, os.path.join(task_name, 'syntax_tree.png'), rankdir="TB")
