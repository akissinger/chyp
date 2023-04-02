from typing import Any, List, Optional, Tuple
from lark import Lark, Transformer, UnexpectedCharacters, UnexpectedEOF, UnexpectedToken, v_args
from lark.tree import Meta
from .graph import Graph, GraphError, gen, perm, identity
from .rule import Rule, RuleError

# class SemanticError(Exception):
#     def __init__(self, line: int, message: str):
#         self.line = line
#         self.message = message
#         super().__init__(str(self.line) + ": " + self.message)

grammar = Lark("""
               start : statement*
               ?statement : gen | let | rule
               gen : "gen" var ":" num "->" num
               let : "let" var "=" term
               rule : "rule" var ":" term "=" term
               ?term  : par_term | seq
               ?par_term : "(" term ")" | par | perm | id | term_ref
               par : par_term "*" par_term
               seq : term ";" term
               perm : "sw" [ "[" num ("," num)* "]" ]
               id : "id"

               num : INT
               var : CNAME
               term_ref : CNAME
               rule_ref : CNAME

               %import common.CNAME
               %import common.INT
               %ignore " "
               %ignore "\\n"
               """,
               parser='lalr',
               propagate_positions=True)

class State:
    def __init__(self):
        self.graphs = dict()
        self.rules = dict()
        self.statements = []
        self.errors = []

    def update(self, code: str):
        try:
            tree = grammar.parse(code)
            tran = ChypTransformer()
            st = tran.transform(tree)

            self.graphs = tran.graphs
            self.rules = tran.rules
            self.statements = st
            self.errors = tran.errors
        except UnexpectedEOF as e:
            self.errors = [(-1, str(e))]
        except UnexpectedToken as e:
            self.errors = [(e.token.line, str(e))]
        except UnexpectedCharacters as e:
            self.errors = [(e.line, str(e))]

    def statement_at(self, pos: int) -> Optional[Tuple[int,int,str,str]]:
        for s in self.statements:
            if s[0] <= pos and s[1] >= pos:
                return s
        return None

class ChypTransformer(Transformer):
    def __init__(self):
        self.graphs = dict()
        self.rules = dict()
        self.errors = list()
    
    def start(self, items: List[Tuple[int,int,str,str]]):
        return items
        
    def var(self, items: List[Any]):
        return str(items[0])
    
    def num(self, items):
        return int(items[0])

    def id(self, _):
        return identity()

    @v_args(meta=True)
    def perm(self, meta: Meta, items: List[Any]) -> Optional[Graph]:
        try:
            if items[0] is None:
                return perm([1,0])
            else:
                return perm([int(i) for i in items])
        except GraphError as e:
            self.errors.append((meta.line, str(e)))
    
    @v_args(meta=True)
    def term_ref(self, meta: Meta, items: List[Any]) -> Optional[Graph]:
        s = str(items[0])
        if s in self.graphs:
            return self.graphs[str(items[0])]
        else:
            self.errors.append((meta.line, 'Undefined term: ' + s))
            return None
    
    def par(self, items) -> Optional[Graph]:
        if items[0] and items[1]:
            return items[0] * items[1]
        else:
            return None
    
    @v_args(meta=True)
    def seq(self, meta: Meta, items: List[Any]) -> Optional[Graph]:
        if items[0] and items[1]:
            g = None
            try:
                g = items[0] >> items[1]
            except GraphError as e:
                self.errors.append((meta.line, str(e)))
            return g

    @v_args(meta=True)
    def gen(self, meta: Meta, items: List[Any]) -> Tuple[int, int, str, str]:
        name, arity, coarity = items
        self.graphs[name] = gen(name, arity, coarity)
        return (meta.start_pos, meta.end_pos, 'gen', name)
        
    @v_args(meta=True)
    def let(self, meta: Meta, items: List[Any]):
        name, graph = items
        if graph:
            self.graphs[name] = graph
        return (meta.start_pos, meta.end_pos, 'let', name)

    @v_args(meta=True)
    def rule(self, meta: Meta, items: List[Any]):
        name, lhs, rhs = items
        if lhs and rhs:
            try:
                self.rules[name] = Rule(lhs, rhs)
            except RuleError as e:
                self.errors.append((meta.line, str(e)))
        return (meta.start_pos, meta.end_pos, 'rule', name)
