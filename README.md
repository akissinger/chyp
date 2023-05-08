Chyp (pronounced "chip") is an interactive theorem prover for symmetric monoidal categories (SMCs), a.k.a. process theories. Symmetric monoidal categories are a very general way to reason about processes that can be composed in sequence or in parallel. String diagrams are a convenient notation for maps in an SMC, where processes are represented as boxes connected to each other by wires.

![Chyp screenshot](https://github.com/akissinger/chyp/raw/master/chyp-screen.png)

Chyp is short for _Composing HYPergraphs_, which refers to how string diagrams are represented and plugged together formally in the tool. By switching to a combinatoric structure based on hypergraphs, we obtain a convenient rewrite theory for string diagrams. There is a lot of theory behind this, which has been developed over a series of papers:

* [String Diagram Rewrite Theory I: Rewriting with Frobenius Structure](https://arxiv.org/abs/2012.01847)
* [String Diagram Rewrite Theory II: Rewriting with Symmetric Monoidal Structure](https://arxiv.org/abs/2104.14686)
* [String diagram rewrite theory III: Confluence with and without Frobenius](https://discovery.ucl.ac.uk/id/eprint/10151067/1/string-diagram-rewrite-theory-iii-confluence-with-and-without-frobenius.pdf)

Currently, Chyp implements the theory described in part II, using monogamous acyclic hypergraphs to represent morphisms in a symmetric monoidal category. Fancier types of rewriting (e.g. rewriting modulo Frobenius structure) is planned for the future.


# Installation

The latest release of Chyp can be installed via [pip](https://pypi.org/project/chyp/) and run from the command line as follows:

```bash
pip install chyp
chyp
```

This will automatically install dependencies: [PySide6](https://pypi.org/project/PySide6/) (Qt6 GUI bindings), [cvxpy](https://www.cvxpy.org/) (a convex solver used for diagram layout), and [lark](https://github.com/lark-parser/lark) (parser library).

To run the latest git version, execute the following commands:

```bash
git clone https://github.com/akissinger/chyp.git
cd chyp
pip install .
python3 -m chyp
```

# Using Chyp

The main way to interact with Chyp is by writing `*.chyp` prover files. These are source files written in a simple declarative language that lets you:
1. define generators,
2. build terms by composing generators,
3. define rewrite rules (i.e. axioms), and
4. prove new rules by rewriting.

## Defining generators and terms

Generators are defined via the `gen` statement, which takes a name, a number of input wires, and a number of output wires. For example, we can define three new generators `f`, `g`, and `h` with various arities as follows:

    gen f : 2 -> 1
    gen g : 1 -> 2
    gen h : 1 -> 1

These can be combined via parallel composition `*` and sequential composition `;`. We can build composed maps from simpler ones using a `let` statement:

    let a = (g * h) ; (h * f)

Parallel composition takes precendence over sequential composition, so the parentheses can be dropped in the above command, which can equivalently be written:

    let a = g * h ; h * f

Any terms can be combined in parallel, but for sequential composition `S ; T` the number of outputs of `S` must match the number of inputs of `T`. There are also special generators `id : 1 -> 1` and `sw : 2 -> 2` corresponding to the identity and swap maps respectively. This enables us to wire boxes up in more complicated ways, like this:

    let b = g * g ; id * sw * id ; f * f

Note that, as you type in the bottom half of the screen, Chyp will automatically update the proof state and the graph view in the top half. This gives instant feedback, which is handy when building complicated terms. As soon as Chyp is able to parse your code, it will highlight to current statement and show the associated diagram(s) on top. To manually check your code, press `CTRL+R`. This is mainly useful for getting useful errors printed in the terminal if something is wrong.

While combining `id` and `sw` suffices for building any permutation of wires, this is not very convenient for more complicated permutations. Hence, there is a more powerful version of `sw` which takes an arbitrary permutation. `sw[x0, x1, ..., xk]` defines the map on `k+1` wires that sends input `xi` to output `i` (counting from 0). `sw` is actually shorthand for `sw[1,0]`. Using this notation, we could equivalently write `b` from above as:

    let b = g * g ; sw[0,2,1,3] ; f * f

Note these indices are local to the swap map, so splitting or combining swap maps will change some indices in general. For example:

    sw[1, 2, 0] * sw[1, 0] = sw[1, 2, 0, 4, 3]


## Rules and rewriting

An algebraic theory can be presented by introducing some generators as well as some rewrite rules. Rules are defined via the `rule` statement, which gives the rule a name, then takes as input a pair of terms with the same number of inputs and outputs. For example, we could introduce a pair of rules relating the `f` and `g` generators as follows:

    rule assoc : f * id ; f = id * f ; f
    rule bialg : f ; g = g * g ; id * sw * id ; f * f

Now for the good part! The `rewrite` statement represents a transitive chain of rule applications. It consists of the keyword `rewrite` followed by a name to use for the resulting theorem, then a sequence of equalities, each giving a justifying rule. For example:

    rewrite ba1 :
      f * id ; f ; g ; g * id
      = id * f ; f ; g ; g * id by assoc
      = g * f ; id * id * g ; id * sw * id ; f * f ; g * id by bialg

Now, when we place the cursor over any step of this rule, it is highlighted in green, and it shows where that rule is applied. The green highlighting is indicating that Chyp has successfully checked this step. Namely, it has matched the LHS of the given rule on the previous term, rewritten the LHS to the RHS, and checked the result is the same as the term given.

The golden rule of Chyp is that _only connectivity matters_. So, if two terms give the same diagram, like `a * b ; c * d` and `(a ; c) * (b ; d)`, Chyp treats them as identical. Since under the hood, Chyp does everything with graph rewriting and not term rewriting, the prover handles all of this extra book-keeping for you.

Note that, if we make a mistake in the example above (e.g. try to replace `assoc` with `bialg` or `sw` with `id * id`), that line will turn red. This means Chyp was _not_ able to find a matching for the rule given which implies the given equality.

## Automatically rewriting terms

Finally, note that it is not so convenient to manually type in the results of rewriting a term. Chyp's solution for this is to introduce "holes", which you can then ask the rewriter to fill. For example, try typing this:

    rewrite ba1 :
      f * id ; f ; g ; g * id
      = ? by assoc

Place your cursor on the last line, which should be red. Then press `CTRL+N` and Chyp will try to find the next matching of the `assoc` rule, apply it, and replace the hole `?` with the result. Since this is now a correct application of the rule, the line will turn green.

Two hotkeys are provided which make adding new rewrite steps easier. `CTRL+Enter` will insert a new line below the current one containing the code `  = ? by ` and place the cursor at the end of the line, ready to take a rule name.

`CTRL+SHIFT+Enter` will insert a new line `  = ? by NAME` where `NAME` is the name of the rule used on the current step, then automatically try to fill the hole. This is handy for repeatedly applying the same rule. For example, try typing this:

    rewrite ba2 :
      id * f ; f ; g ; id * g
      = ? by bialg

Then press `CTRL+N`, followed by `CTRL+SHIFT+Enter` 3 times, and Chyp will compute the normal form with respect to the `bialg` rule:

    rewrite ba2 :
      id * f ; f ; g ; id * g
      = g * f ; id * id * g ; id * sw * id ; f * f ; id * g by bialg
      = g * g * g ; id * id * id * sw * id ; id * id * f * f ; id * sw * id ; f * f ; id * g by bialg
      = g * g * g ; id * id * id * sw * id ; id * g * f * f ; sw * sw * id ; id * f * id * g ; sw * sw * id ; id * f * f by bialg
      = g * g * g ; id * id * id * sw * id ; id * g * f * g * g ; sw * sw * id * sw * id ; id * f * id * f * f ; sw * sw * id ; id * f * f by bialg

How to we know it's a normal form? Pressing `CTRL+SHIFT+Enter` one more time will result in a red line that reads `  = ? by bialg`, which means Chyp wasn't able to find any more matchings of the `bialg` rule.

# Grammar

The Chyp language is very small. The full grammar, which is essentially the one used in [chyp/parser.py](https://github.com/akissinger/chyp/blob/master/chyp/parser.py), is the following:

```lark

start : statement*
statement : gen | let | rule | rewrite
gen : "gen" var ":" num "->" num
let : "let" var "=" term
rule : "rule" var ":" term "=" term
rewrite : "rewrite" var ":" term rewrite_part*
rewrite_part : "=" term_hole "by" inverse? rule_ref
inverse : "-"
term  : par_term | seq
par_term : "(" term ")" | par | perm | id | term_ref
par : par_term "*" par_term
seq : term ";" term
perm : "sw" ( "[" num ("," num)* "]" )?
id : "id"
term_hole : term | "?"

num : INT
var : IDENTIFIER
term_ref : IDENTIFIER
rule_ref : IDENTIFIER

```

The parser ignores whitespace and comments starting with `#`.

