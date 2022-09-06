# chyp

`chyp` (pronounced "chip") is a Python library for viewing, editing, and rewriting hypergraphs. It is especially intended for use with hypergraphs with boundaries, which are used to represent processes with inputs and outputs. The 'C' is for "compositional", meaning it makes sense for these kinds of hypergraphs to get plugged into one other, representing the composition of processes.

This library is at an early stage, and mainly intended as a testbed for some ideas or to be incorporated in other tools/libraries.

For those interested in the mathematics behind this library: hypergraphs with boundaries are the combinatoric cousins of _string diagrams_, a graphical notation for morphisms in a symmetric monoidal category. By switching to a combinatoric structure based on hypergraphs, we obtain a convenient rewrite theory for string diagrams. This is developed over a series of papers:

* [String Diagram Rewrite Theory I: Rewriting with Frobenius Structure](https://arxiv.org/abs/2012.01847)
* [String Diagram Rewrite Theory II: Rewriting with Symmetric Monoidal Structure](https://arxiv.org/abs/2104.14686)
* [String diagram rewrite theory III: Confluence with and without Frobenius](https://discovery.ucl.ac.uk/id/eprint/10151067/1/string-diagram-rewrite-theory-iii-confluence-with-and-without-frobenius.pdf)
