# chyp

`chyp` (pronounced "chip") is a Python library for viewing, editing, and rewriting hypergraphs. It is especially intended for use with hypergraphs with boundaries, which are used to represent processes with inputs and outputs. The 'C' is for "compositional", meaning it makes sense for these kinds of hypergraphs to get plugged into one other, representing the composition of processes.

The main classes provided by the library are the `Graph` datatype of hypergraphs (note the prefix "hyper-" is omitted from hypergraph and hyperedge everywhere) and the PyQt6 `GraphView` widget. Here's an example of their use, assuming `w` is the Qt widget where you want to add the `GraphView`:

```python
from chyp import Graph, GraphView

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

This will produce a hypergraph view with draggable nodes and boxes that looks like this:
![Hypergraph example](https://github.com/akissinger/chyp/raw/master/example.png)

This library is at an early stage, and mainly intended as a testbed for some ideas or to be incorporated in other tools/libraries.

For those interested in the mathematics behind this library: hypergraphs with boundaries are the combinatoric cousins of _string diagrams_, a graphical notation for morphisms in a symmetric monoidal category. By switching to a combinatoric structure based on hypergraphs, we obtain a convenient rewrite theory for string diagrams. This is developed over a series of papers:

* [String Diagram Rewrite Theory I: Rewriting with Frobenius Structure](https://arxiv.org/abs/2012.01847)
* [String Diagram Rewrite Theory II: Rewriting with Symmetric Monoidal Structure](https://arxiv.org/abs/2104.14686)
* [String diagram rewrite theory III: Confluence with and without Frobenius](https://discovery.ucl.ac.uk/id/eprint/10151067/1/string-diagram-rewrite-theory-iii-confluence-with-and-without-frobenius.pdf)
