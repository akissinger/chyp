#     chyp - An interactive theorem prover for string diagrams 
#     Copyright (C) 2022 - Aleks Kissinger
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os.path
from typing import Dict, Optional, Tuple
from lark import Lark, UnexpectedInput, Tree

from . import state

GRAMMAR = Lark("""
    start : statement*
    ?statement : import_statement | gen | let | def_statement | rule | rewrite | show | theorem_statement
    gen : "gen" var ":" type_term "->" type_term [ gen_color ]
    def_statement : "def" var "=" term [ gen_color ]
    gen_color : "\\\"" color "\\\"" | "\\\"" color "\\\"" "\\\"" color "\\\""
    let : "let" var "=" term
    rule : "rule" var ":" term (eq | le) term
    rewrite : "rewrite" [converse] var ":" term rewrite_part*
    rewrite_pf : "rewrite" rewrite_side rewrite_part*
    rewrite_side : "LHS" | "RHS"
    rewrite_part : (eq | le) term_hole [ "by" tactic ]
    converse : "-"
    ?theorem_statement : theorem [ proof ]
    theorem : ("theorem" | "lemma" | "proposition") var ":" formula
    formula : term (eq | le) term
    proof : proof_start proof_step* proof_end
    proof_start : "proof"
    proof_end: "qed"
    ?proof_step : apply_tac | rewrite_pf
    apply_tac : "apply" tactic

    type_term : type_element ("*" type_element)* | num
    type_element: IDENT ["^" num]

    LPAREN: "("
    RPAREN: ")"
    tactic : [ converse ] IDENT | IDENT LPAREN [ TACTIC_ARG ("," TACTIC_ARG)* ] ")"
    ?term  : par_term | seq
    ?par_term : nested_term | par | perm | id | id0
              | redistribution | term_ref
    nested_term : LPAREN term RPAREN
    par : par_term "*" par_term
    seq : term ";" term
    perm : "sw" [ "[" type_term "]" ] [ "[" perm_indices "]" ]
    perm_indices : num ("," num)+
    id : "id" [ "[" type_element "]" ]
    id0 : "id0"
    redistribution : "rd" ["[" IDENT "]"]("[" size_list "to" size_list "]")
    size_list: num ("," num)*
    show : "show" rule_ref

    import_statement : "import" module_name [ "as" var ] [ "(" import_let ("," import_let)* ")" ]
    import_let : var "=" term

    eq : "=" | "=="
    le : "<=" | "~>"
    num : INT
    module_name : IDENT
    var : IDENT
    term_ref : IDENT
    rule_ref : IDENT
    term_hole : term | "?"
    color : HEXDIGIT HEXDIGIT HEXDIGIT HEXDIGIT HEXDIGIT HEXDIGIT
    IDENT: ("_"|LETTER) ("_"|"."|LETTER|DIGIT)*
    TACTIC_ARG: /[^(),]+/

    %import common.LETTER
    %import common.DIGIT
    %import common.HEXDIGIT
    %import common.INT
    %import common.WS
    %import common.SH_COMMENT
    %ignore WS
    %ignore SH_COMMENT
    """,
    parser='lalr',
    propagate_positions=True,
    maybe_placeholders=True)


# cache parse trees for imported files and only re-parse if the file changes
parse_cache: Dict[str, Tuple[float, Tree]] = dict()

def parse(code: str='', file_name: str='', namespace: str='', parent: Optional[state.State] = None) -> state.State:
    global parse_cache

    old_namespace = ''
    if parent:
        old_namespace = parent.namespace
        if namespace != '':
            parent.namespace = parent.namespace + '.' + namespace
        parent.import_depth += 1
        if parent.import_depth > 255:
            parent.errors += [(parent.file_name, -1, "Maximum import depth (255) exceeded. Probably a cyclic import.")]
        parse_data = parent
    else:
        parse_data = state.State(namespace, file_name)

    # if parent:
    #     parse_data.graphs = parent.graphs
    #     parse_data.rules = parent.rules
    #     parse_data.rewrites = parent.rewrites
    #     parse_data.errors = parent.errors
    #     parse_data.rule_sequence = parent.rule_sequence
    #     parse_data.sequence = parent.sequence
    #     parse_data.import_depth = parent.import_depth + 1
    #     if parse_data.import_depth > 255:
    #         parse_data.errors += [(parent.file_name, -1, "Maximum import depth (255) exceeded. Probably a cyclic import.")]

    try:
        if file_name and not code:
            mtime = os.path.getmtime(file_name)
            if file_name in parse_cache and parse_cache[file_name][0] == mtime:
                tree = parse_cache[file_name][1]
            else:
                with open(file_name) as f:
                    tree = GRAMMAR.parse(f.read())
                parse_cache[file_name] = (mtime, tree)
        else:
            tree = GRAMMAR.parse(code)
        parse_data.transform(tree)
    except UnexpectedInput as e:
        msg = 'Parse error: '
        e_lines = e.get_context(code).splitlines()
        if len(e_lines) >= 2:
            parse_data.errors += [(file_name, e.line, msg + e_lines[0] + '\n' + len(msg)*' ' + e_lines[1])]
        else:
            parse_data.errors += [(file_name, e.line, msg + e_lines[0])]

    if parent:
        parent.import_depth -= 1
        parent.namespace = old_namespace
    else:
        parse_data.parsed = True

    return parse_data

