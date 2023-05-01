`Chyp` (pronounced "chip") is an interactive theorem prover for symmetric monoidal categories (SMCs), a.k.a. process theories. Symmetric monoidal categories are a very general way to reason about processes that can be composed in sequence or in parallel. String diagrams are a convenient notation for maps in an SMC, where processes are represented as boxes connected to each other by wires.

![Chyp screenshot](https://github.com/akissinger/chyp/raw/master/chyp-screen.png)

Chyp is short for _Composing HYPergraphs_, which refers to how string diagrams are represented and plugged together formally in the tool. By switching to a combinatoric structure based on hypergraphs, we obtain a convenient rewrite theory for string diagrams. There is a lot of theory behind this, which has been developed over a series of papers:

* [String Diagram Rewrite Theory I: Rewriting with Frobenius Structure](https://arxiv.org/abs/2012.01847)
* [String Diagram Rewrite Theory II: Rewriting with Symmetric Monoidal Structure](https://arxiv.org/abs/2104.14686)
* [String diagram rewrite theory III: Confluence with and without Frobenius](https://discovery.ucl.ac.uk/id/eprint/10151067/1/string-diagram-rewrite-theory-iii-confluence-with-and-without-frobenius.pdf)

# Installation

Chyp can be installed using `pip` as follows:

```bash
git clone https://github.com/akissinger/chyp.git
cd chyp
pip install .
```

It can then be run by running `chyp` from the command line or `python3 -m chyp` from inside the source directory.



# Using `chyp` as a library

While the main purpose of `chyp` is to be a standalone interactive theorem prover, it is also designed to be a useful library for hacking and experimenting with hypergraph/SMC rewriting, and drawing the results.

Here's an example of building a small hypergraph using the `Graph` datatype, and drawing it with the PyQt5 `GraphView` widget, assuming `w` is the Qt widget where you want to add the `GraphView`.

```python
from chyp import *

# ...

g = Graph()
v0 = g.add_vertex(-4, 1)
v1 = g.add_vertex(-4, -1)
v2 = g.add_vertex(0, 0)
v3 = g.add_vertex(4, 2)
v4 = g.add_vertex(4, 0)
v5 = g.add_vertex(4, -2)
g.add_edge([v0, v1], [v2], -2, 0, "f")
g.add_edge([v2], [v3,v4,v5], 2, 0, "g")
g.add_edge([v3], [], 6, 2, "x")
g.add_edge([v4], [], 6, 0, "y")

view = GraphView()
view.set_graph(g)

w.layout().addWidget(view)
```

Note the prefix "hyper-" is omitted from hypergraph and hyperedge everywhere in the code. This will produce a hypergraph view with draggable nodes and boxes that looks like this:
![Hypergraph example](https://github.com/akissinger/chyp/raw/master/example.png)


### Rewriting

`chyp` implements double-pushout (DPO) rewriting. In order to rewrite a graph one first constructs a _rule_, which consists of a pair of hypergraphs-with-boundary with the same number of inputs and outputs:

```python
from chyp import *

g1 = Graph()
w0 = g1.add_vertex(0, 0)
w1 = g1.add_vertex(2, 1)
w2 = g1.add_vertex(2, 0)
w3 = g1.add_vertex(2, -1)
g1.add_edge([w0], [w1, w2, w3], 1, 0, "g")
g1.add_edge([w1], [], 2, 0, "x")
g1.set_inputs([w0])
g1.set_outputs([w2, w3])

g2 = Graph()
w0 = g2.add_vertex(0, 0)
w1 = g2.add_vertex(2, 0)
w2 = g2.add_vertex(2, -1)
g2.add_edge([w0], [w1, w2], 2, 0, "h")
g2.set_inputs([w0])
g2.set_outputs([w1, w2])

r = Rule(g1, g2)
```

In order to apply a rule, it must be _matched_, i.e. one must find an embedding of the lefthand-side `r.lhs` into `g`. Matches can be found using the `match_rule` method:

```python
def match_rule(r: Rule, g: Graph) -> Iterable[Match]
```

This returns an `Iterable` containing a `Match` object for each of the possible matches of `r.lhs` into `g`. There could be very many of these, so they are computed lazily.

Once a match is found, the rewritten graph can be calculated via the `rewrite` function:

```python
ms = list(match_rule(r, g))
if len(ms) != 0:
    print(ms[0])
    h = rewrite(r, ms[0])
else:
    print("no matches")
```

The `rewrite` method is a thin wrapper around the `dpo` function, which returns a sequence of rewrites possible for rule `r` at match `m`. If `r` is left-linear, this will always return just one rewrite. A "rewrite" here means a new `Match` object that embeds `r.rhs` into the rewritten graph `h`. 

```python
def dpo(r: Rule, m: Match) -> Iterable[Match]
```

This is sometimes useful, i.e. for visualising the part of the graph that has been updated or verifying that a rewrite was performed correctly.

For times when this embedding isn't required, `rewrite` simply returns the codomain of the embedding, i.e. the rewritten graph itself:

```python
def rewrite(r: Rule, m: Match) -> Graph:
    result = next(iter(dpo(r, m))
    return result.cod
```


