from typing import Any, Dict, List, Optional, Tuple
from lark import Lark, Transformer, UnexpectedCharacters, UnexpectedEOF, UnexpectedToken, v_args
from lark.tree import Meta

from .graph import Graph, GraphError, gen, perm, identity
from .rule import Rule, RuleError

GRAMMAR = Lark("""
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

class ChypParseData(Transformer):

    def __init__(self) -> None:
        self.graphs: Dict[str, Graph] = dict()
        self.rules: Dict[str, Rule] = dict()
        self.rewrites: Dict[str, Tuple[int, int, Optional[Rule], Optional[Graph], Optional[Graph]]] = dict()
        self.errors: List[Tuple[int, str]] = list()
        self.parts: List[Tuple[int, int, str, str]] = list()
        self.parsed = False
    
    # def start(self, items: List[List[Tuple[int,int,str,str]]]):
    #     pass
        
    def var(self, items: List[Any]) -> str:
        return str(items[0])
    
    def num(self, items: List[Any]) -> int:
        return int(items[0])

    def id(self, _: List[Any]) -> Graph:
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
        return None
    
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
    
    def par(self, items: List[Any]) -> Optional[Graph]:
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
        else:
            return None

    @v_args(meta=True)
    def gen(self, meta: Meta, items: List[Any]) -> None:
        name, arity, coarity = items
        self.graphs[name] = gen(name, arity, coarity)
        self.parts.append((meta.start_pos, meta.end_pos, 'gen', name))
        
    @v_args(meta=True)
    def let(self, meta: Meta, items: List[Any]) -> None:
        name, graph = items
        if graph:
            self.graphs[name] = graph
        self.parts.append((meta.start_pos, meta.end_pos, 'let', name))

    @v_args(meta=True)
    def rule(self, meta: Meta, items: List[Any]) -> None:
        name, lhs, rhs = items
        if lhs and rhs:
            try:
                self.rules[name] = Rule(lhs, rhs, name=name)
            except RuleError as e:
                self.errors.append((meta.line, str(e)))
        self.parts.append((meta.start_pos, meta.end_pos, 'rule', name))

    @v_args(meta=True)
    def rewrite(self, meta: Meta, items: List[Any]) -> None:
        name = items[0]
        term = items[1]
        rw_parts = items[2:]

        if len(rw_parts) == 0:
            self.parts.append((meta.start_pos, meta.end_pos, "rewrite", name))
            self.rewrites[name] = (0,0,None,term,None)
        else:
            start = meta.start_pos
            lhs = term
            rhs = None
            for i, rw_part in enumerate(rw_parts):
                end, t_start, t_end, rule, rhs = rw_part
                self.rewrites[name + ":" + str(i)] = (t_start, t_end, rule, lhs, rhs)
                lhs = rhs.copy() if rhs else None
                self.parts.append((start, end, "rewrite", name + ":" + str(i)))
                start = end
            if rhs:
                self.rules[name] = Rule(term, rhs, name)

    @v_args(meta=True)
    def rewrite_part(self, meta: Meta, items: List[Any]) -> Tuple[int, int, int, Rule, Graph]:
        t_start,t_end,rhs = items[0]
        rule = items[1]
        return (meta.end_pos, t_start, t_end, rule, rhs)


    @v_args(meta=True)
    def term_hole(self, meta: Meta, items: List[Any]) -> Tuple[int, int, Optional[Graph]]:
        t = items[0] if len(items) != 0 else None
        return (meta.start_pos, meta.end_pos, t)

def parse(code: str) -> ChypParseData:
    parse_data = ChypParseData()
    try:
        tree = GRAMMAR.parse(code)
        parse_data.transform(tree)
        parse_data.parsed = True
    except UnexpectedEOF as e:
        parse_data.errors += [(-1, str(e))]
    except UnexpectedToken as e:
        parse_data.errors += [(e.token.line, str(e))]
    except UnexpectedCharacters as e:
        parse_data.errors += [(e.line, str(e))]

    return parse_data

