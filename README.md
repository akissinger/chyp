# chyp

`chyp` (pronounced "chip") is a Python library for viewing, editing, and rewriting hypergraphs. It is especially intended for use with hypergraphs with boundaries, which are used to represent processes with inputs and outputs. The 'C' is for "compositional", meaning it makes sense for these kinds of hypergraphs to get plugged into one other, representing the composition of processes.

Here's an example of building a small hypergraph using the `Graph` datatype, and drawing it with the PyQt6 `GraphView` widget, assuming `w` is the Qt widget where you want to add the `GraphView`.

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

For those interested in the mathematics behind this library: hypergraphs with boundaries are the combinatoric cousins of _string diagrams_, a graphical notation for morphisms in a symmetric monoidal category. By switching to a combinatoric structure based on hypergraphs, we obtain a convenient rewrite theory for string diagrams. This is developed over a series of papers:

* [String Diagram Rewrite Theory I: Rewriting with Frobenius Structure](https://arxiv.org/abs/2012.01847)
* [String Diagram Rewrite Theory II: Rewriting with Symmetric Monoidal Structure](https://arxiv.org/abs/2104.14686)
* [String diagram rewrite theory III: Confluence with and without Frobenius](https://discovery.ucl.ac.uk/id/eprint/10151067/1/string-diagram-rewrite-theory-iii-confluence-with-and-without-frobenius.pdf)

## Rewriting

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

The `rewrite` method is a thin wrapper around the `dpo` function, which will return a new `Match` object that embeds `r.rhs` into the rewritten graph `h`.

```python
def dpo(r: Rule, m: Match) -> Match
```

This is sometimes useful, i.e. for visualising the part of the graph that has been updated or verifying that a rewrite was performed correctly.

For times when this embedding isn't required, `rewrite` simply returns the codomain of the embedding, i.e. the rewritten graph itself:

```python
def rewrite(r: Rule, m: Match) -> Graph:
    m1 = dpo(r, m)
    return m1.cod
```


## TODO

This library is at an early stage, and mainly intended as a testbed for some ideas or to be incorporated in other tools/libraries. Here's some things that would be nice to implement:

- [X] building hypergraphs in code
- [X] hypergraph viewer widget
- [X] defining hypergraph rewrite rules
- [X] matching and rewriting hypergraphs
- [ ] GUI graph editing
- [ ] rewriting rules that are not left-linear (i.e. giving multiple results for same match)
- [ ] load/save hypergraphs and rules
- [ ] load/save derivations (a la [Quantomatic](http://quantomatic.github.io))?
- [ ] some basic strategy support?
