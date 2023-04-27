from typing import Any, Dict, List, Optional, Tuple
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
               ?statement : gen | let | rule | rewrite
               gen : "gen" var ":" num "->" num
               let : "let" var "=" term
               rule : "rule" var ":" term "=" term
               rewrite : "rewrite" var ":" term rewrite_part*
               rewrite_part : "=" term_hole "by" rule_ref num?
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
               term_hole : term | "?"

               %import common.CNAME
               %import common.INT
               %ignore " "
               %ignore "\\n"
               """,
               parser='lalr',
               propagate_positions=True)

class RewriteState:
    UNCHECKED = 0
    CHECKING = 1
    VALID = 2
    INVALID = 3

    def __init__(self, term_pos: Tuple[int,int], rule: Optional[Rule], lhs: Graph, rhs: Optional[Graph]):
        self.status = RewriteState.UNCHECKED
        self.term_pos = term_pos
        self.rule = rule if rule else Rule(Graph(), Graph())
        self.lhs = lhs
        self.rhs = rhs if rhs else Graph()

class State:
    def __init__(self):
        self.graphs: Dict[str, Graph] = dict()
        self.rules: Dict[str, Rule] = dict()
        self.rewrites: Dict[str, RewriteState] = dict()
        self.parts = []
        self.errors = []

    def update(self, code: str):
        try:
            tree = grammar.parse(code)
            tran = ChypTransformer()
            parts = tran.transform(tree)

            self.graphs = tran.graphs
            self.rules = tran.rules
            self.rewrites = tran.rewrites
            self.parts = parts
            self.errors = tran.errors
        except UnexpectedEOF as e:
            self.errors = [(-1, str(e))]
        except UnexpectedToken as e:
            self.errors = [(e.token.line, str(e))]
        except UnexpectedCharacters as e:
            self.errors = [(e.line, str(e))]

    def part_at(self, pos: int) -> Optional[Tuple[int,int,str,str]]:
        p0 = None
        for p in self.parts:
            if p[0] <= pos:
                p0 = p
                if p[1] >= pos:
                    return p
        return p0

class ChypTransformer(Transformer):
    def __init__(self):
        self.graphs = dict()
        self.rules = dict()
        self.rewrites = dict()
        self.errors = list()
    
    def start(self, items: List[List[Tuple[int,int,str,str]]]) -> List[Tuple[int,int,str,str]]:
        return [part for item in items for part in item]
        
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

    @v_args(meta=True)
    def rule_ref(self, meta: Meta, items: List[Any]) -> Optional[Rule]:
        s = str(items[0])
        if s in self.rules:
            return self.rules[str(items[0])]
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
    def gen(self, meta: Meta, items: List[Any]):
        name, arity, coarity = items
        self.graphs[name] = gen(name, arity, coarity)
        return [(meta.start_pos, meta.end_pos, 'gen', name)]
        
    @v_args(meta=True)
    def let(self, meta: Meta, items: List[Any]):
        name, graph = items
        if graph:
            self.graphs[name] = graph
        return [(meta.start_pos, meta.end_pos, 'let', name)]

    @v_args(meta=True)
    def rule(self, meta: Meta, items: List[Any]):
        name, lhs, rhs = items
        if lhs and rhs:
            try:
                self.rules[name] = Rule(lhs, rhs, name=name)
            except RuleError as e:
                self.errors.append((meta.line, str(e)))
        return [(meta.start_pos, meta.end_pos, 'rule', name)]

    @v_args(meta=True)
    def rewrite(self, meta: Meta, items: List[Any]):
        name = items[0]
        term = items[1]
        rw_parts = items[2:]

        if len(rw_parts) == 0:
            parts = [(meta.start_pos, meta.end_pos, "rewrite", name)]
            self.rewrites[name] = RewriteState((0, 0), rule=None, lhs=term, rhs=None)
        else:
            parts = []
            start = meta.start_pos
            lhs = term
            for i, rw_part in enumerate(rw_parts):
                end, (t_start, t_end, rule, rhs) = rw_part
                self.rewrites[name + ":" + str(i)] = RewriteState((t_start, t_end), rule, lhs, rhs)
                lhs = rhs
                parts.append((start, end, "rewrite", name + ":" + str(i)))
                start = end

        return parts

    @v_args(meta=True)
    def rewrite_part(self, meta: Meta, items: List[Any]):
        t_start,t_end,rhs = items[0]
        rule = items[1]
        return (meta.end_pos, (t_start, t_end, rule, rhs))


    @v_args(meta=True)
    def term_hole(self, meta: Meta, items: List[Any]):
        t = items[0] if len(items) != 0 else None
        return (meta.start_pos, meta.end_pos, t)
