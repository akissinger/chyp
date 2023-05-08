from typing import Any, Dict, List, Optional, Tuple
from lark import Lark, Transformer, UnexpectedInput, v_args
from lark.tree import Meta

from .graph import Graph, GraphError, gen, perm, identity
from .rule import Rule, RuleError

GRAMMAR = Lark("""
    start : statement*
    ?statement : gen | let | rule | rewrite
    gen : "gen" var ":" num "->" num
    let : "let" var "=" term
    rule : "rule" var ":" term (eq | le) term
    rewrite : "rewrite" [converse] var ":" term rewrite_part*
    rewrite_part : (eq | le) term_hole [ "by" [converse] rule_ref ]
    converse : "-"
    ?term  : par_term | seq
    ?par_term : "(" term ")" | par | perm | id | term_ref
    par : par_term "*" par_term
    seq : term ";" term
    perm : "sw" [ "[" num ("," num)* "]" ]
    id : "id"

    eq : "=" | "=="
    le : "<=" | "~>"
    num : INT
    var : CNAME
    term_ref : CNAME
    rule_ref : CNAME
    term_hole : term | "?"

    %import common.CNAME
    %import common.INT
    %import common.WS
    %import common.SH_COMMENT
    %ignore WS
    %ignore SH_COMMENT
    """,
    parser='lalr',
    propagate_positions=True,
    maybe_placeholders=True)

class ChypParseData(Transformer):

    def __init__(self) -> None:
        self.graphs: Dict[str, Graph] = dict()
        self.rules: Dict[str, Rule] = {'refl': Rule(Graph(), Graph(), name="refl")}
        self.rewrites: Dict[str, Tuple[int, int, bool, Optional[Rule],
                                       Optional[Graph], Optional[Graph],
                                       Optional[Graph], Optional[Graph]]] = dict()
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

    def eq(self, _: List[Any]) -> bool:
        return True

    def le(self, _: List[Any]) -> bool:
        return False

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
            self.errors.append((meta.line, 'Undefined rule: ' + s))
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
        if not name in self.graphs:
            self.graphs[name] = gen(name, arity, coarity)
        else:
            self.errors.append((meta.line, "Term '{}' already defined.".format(name)))
        self.parts.append((meta.start_pos, meta.end_pos, 'gen', name))
        
    @v_args(meta=True)
    def let(self, meta: Meta, items: List[Any]) -> None:
        name, graph = items
        if not name in self.graphs:
            if graph:
                self.graphs[name] = graph
        else:
            self.errors.append((meta.line, "Term '{}' already defined.".format(name)))
        self.parts.append((meta.start_pos, meta.end_pos, 'let', name))

    @v_args(meta=True)
    def rule(self, meta: Meta, items: List[Any]) -> None:
        name, lhs, invertible, rhs = items
        if not name in self.rules:
            if lhs and rhs:
                try:
                    self.rules[name] = Rule(lhs, rhs, name, invertible)
                except RuleError as e:
                    self.errors.append((meta.line, str(e)))
        else:
            self.errors.append((meta.line, "Rule '{}' already defined.".format(name)))
        self.parts.append((meta.start_pos, meta.end_pos, 'rule', name))

    @v_args(meta=True)
    def rewrite(self, meta: Meta, items: List[Any]) -> None:
        converse = True if items[0] else False
        base_name = items[1]
        name = '-' + base_name if converse else base_name

        term = items[2]
        rw_parts = items[3:]

        if len(rw_parts) == 0:
            self.parts.append((meta.start_pos, meta.end_pos, "rewrite", name))
            self.rewrites[name] = (0,0,False,None,term,None,None,None)
        else:
            start = meta.start_pos
            lhs = term
            rhs = None
            all_equiv = True

            if converse and base_name in self.rules:
                lhs_match = self.rules[base_name].rhs
                rhs_match = self.rules[base_name].lhs
            else:
                lhs_match = None
                rhs_match = None

            last_i = len(rw_parts)-1
            for i, rw_part in enumerate(rw_parts):
                end, t_start, t_end, equiv, rule, rhs = rw_part
                all_equiv = all_equiv and equiv
                self.rewrites[name + ":" + str(i)] = (t_start, t_end, equiv, rule, lhs, rhs,
                                                      lhs_match if i == 0 else None,
                                                      rhs_match if i == last_i else None)
                lhs = rhs.copy() if rhs else None
                self.parts.append((start, end, "rewrite", name + ":" + str(i)))
                start = end
            if term and rhs:
                try:
                    if converse:
                        if base_name in self.rules:
                            self.rules[base_name].equiv = True
                        else:
                            self.errors.append((meta.line, "Trying to prove converse for unknown rule: " + base_name))
                    else:
                        if not name in self.rules:
                            self.rules[name] = Rule(term, rhs, name=name, equiv=all_equiv)
                        else:
                            self.errors.append((meta.line, "Rule '{}' already defined.".format(name)))
                except RuleError as e:
                    self.errors.append((meta.line, str(e)))

    @v_args(meta=True)
    def rewrite_part(self, meta: Meta, items: List[Any]) -> Tuple[int, int, int, bool, Optional[Rule], Optional[Graph]]:
        equiv = items[0]
        t_start,t_end,rhs = items[1]
        converse = True if items[2] else False

        rule = items[3] if items[3] else self.rules['refl']
        if rule and converse:
            rule = items[3].converse()

        if equiv and rule and not rule.equiv:
            rule = None

        return (meta.end_pos, t_start, t_end, equiv, rule, rhs)


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
    except UnexpectedInput as e:
        msg = 'Parse error: '
        e_lines = e.get_context(code).splitlines()
        if len(e_lines) >= 2:
            parse_data.errors += [(e.line, msg + e_lines[0] + '\n' + len(msg)*' ' + e_lines[1])]
        else:
            parse_data.errors += [(e.line, msg + e_lines[0])]

    # except UnexpectedToken as e:
    #     parse_data.errors += [(e.line, "Parse error, unexpected token:\n" + e.get_context(code))]
    # except UnexpectedCharacters as e:
    #     parse_data.errors += [(e.line, "Parse error, unexpected characters:\n" + e.get_context(code))]

    return parse_data

