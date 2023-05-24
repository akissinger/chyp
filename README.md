Chyp (pronounced "chip") is an interactive theorem prover for symmetric monoidal categories (SMCs), a.k.a. process theories. Symmetric monoidal categories are a very general way to reason about processes that can be composed in sequence or in parallel. String diagrams are a convenient notation for maps in an SMC, where processes are represented as boxes connected to each other by wires.

![Chyp screenshot](https://github.com/akissinger/chyp/raw/master/chyp-screen.png)

Chyp is short for _Cospans of HYPergraphs_, which refers to how string diagrams are represented and plugged together formally in the tool. By switching from terms to this combinatoric structure, we obtain a convenient rewrite theory for string diagrams that automatically handles the extra "bureaucracy" that comes from working with sequential and parallel composition together. There is a lot of theory behind this, which has been developed over a series of papers:

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

You can find some examples of `*.chyp` files in the [examples](https://github.com/akissinger/chyp/tree/master/examples) folder.

## Defining generators and terms

Generators are defined via the `gen` statement, which takes a name, a number of input wires, and a number of output wires. For example, we can define three new generators `f`, `g`, and `h` with various arities as follows:

    gen f : 2 -> 1
    gen g : 1 -> 2
    gen h : 1 -> 1

These can be given a colors by providing one or two hex codes after the definition, defining the background and forground color, respectively:

    gen f : 2 -> 1 "00ff00"            # green background, default (black) foreground
    gen g : 1 -> 2 "000000" "ffffff"   # black background, white foreground
    gen h : 1 -> 1 "0000ff" "0000ff"   # blue background, blue foreground (i.e. hidden text)

Generators can be combined via parallel composition `*` and sequential composition `;`. We can build composed maps from simpler ones using a `let` statement:

    let a = (g * h) ; (h * f)

Parallel composition takes precendence over sequential composition, so the parentheses can be dropped in the above command, which can equivalently be written:

    let a = g * h ; h * f

Any terms can be combined in parallel, but for sequential composition `S ; T` the number of outputs of `S` must match the number of inputs of `T`. There are also special generators `id : 1 -> 1` and `sw : 2 -> 2` corresponding to the identity and swap maps respectively. This enables us to wire boxes up in more complicated ways, like this:

    let b = g * g ; id * sw * id ; f * f

There is also a special generator `id0 : 0 -> 0`, corresponding to the empty diagram, i.e. the "identity" process on zero wires.

Note that, as you type in the bottom half of the screen, Chyp will automatically update the proof state and the graph view in the top half. This gives instant feedback, which is handy when building complicated terms. As soon as Chyp is able to parse your code, it will highlight to current statement and show the associated diagram(s) on top. To manually check your code, press `CTRL+R`. This is mainly useful for getting useful errors printed in the terminal if something is wrong.

While combining `id` and `sw` suffices for building any permutation of wires, this is not very convenient for more complicated permutations. Hence, there is a more powerful version of `sw` which takes an arbitrary permutation. `sw[x0, x1, ..., xk]` defines the map on `k+1` wires that sends input `xi` to output `i` (counting from 0). `sw` is actually shorthand for `sw[1, 0]`. Using this notation, we could equivalently write `b` from above as:

    let b = g * g ; sw[0, 2, 1, 3] ; f * f

Note these indices are local to the swap map, so splitting or combining swap maps will change some indices in general. For example:

    sw[1, 2, 0] * sw[1, 0] = sw[1, 2, 0, 4, 3]

The `def` statement is a close cousin to the `let` statement, but its behavior is slightly different. If we change `let` to `def` in the example above, we get:

    def a = g * h ; h * f

Before, when we used `a` in another term, it would immediately be expanded to the RHS, but now if we use `a`, e.g. in:

    let x = a ; a
    
we'll just see two `a`-labelled boxes. This is because, behind the scenes `def` introduces a new generator called `a` and a new rule, called `a_def`, that can be used to explicitly fold/unfold `a` in a proof.

To see how this works, we'll first need to introduce rules and rewriting.


## Rules and rewriting


An algebraic theory can be presented by introducing some generators as well as some rewrite rules. Rules are defined via the `rule` statement, which gives the rule a name, then takes as input a pair of terms with the same number of inputs and outputs. For example, we could introduce a pair of rules relating the `f` and `g` generators as follows:

    rule assoc : f * id ; f = id * f ; f
    rule bialg : f ; g = g * g ; id * sw * id ; f * f

Now for the good part! The `rewrite` statement represents a transitive chain of rule applications. It consists of the keyword `rewrite` followed by a name to use for the resulting theorem, then a sequence of equalities, each giving a justifying rule. For example:

    rewrite ba1 :
      f * id ; f ; g ; g * id
      = id * f ; f ; g ; g * id by assoc
      = g * f ; id * id * g ; id * sw * id ; f * f ; g * id by bialg

Now, when we place the cursor over any step of this rule, it is highlighted in green, and it shows where that rule is applied. The green highlighting is indicating that Chyp has successfully checked this step. Namely, it has matched the LHS of the given rule on the previous term, rewritten the LHS to the RHS, and checked the result is the same as the term given. If we make a mistake in the example above (e.g. try to replace `assoc` with `bialg` or `sw` with `id * id`), that line will turn red. This means Chyp was _not_ able to find a matching for the rule given which implies the given equality.

By default, Chyp tries to apply rules from left to right. We can apply a rule in the other direction by prefixing the rule name with `-`. For example, the proof above can be done backwards as follows:

    rewrite ba1_backwards :
      g * f ; id * id * g ; id * sw * id ; f * f ; g * id
      = id * f ; f ; g ; g * id by -bialg
      = f * id ; f ; g ; g * id by -assoc

The golden rule of Chyp is that _only connectivity matters_. So, if two terms give the same diagram, like `a * b ; c * d` and `(a ; c) * (b ; d)`, Chyp treats them as identical. Since under the hood, Chyp does everything with graph rewriting and not term rewriting, the prover handles all of this extra book-keeping for you.

Sometimes it can be helpful for readability to do a trivial proof step that does nothing but write the same string diagram differently. There is a special rule called `refl` (for reflexivity) for this. For example:

    rewrite foo :
      a * b ; c * d
      = (a ; c) * (b ; d) by refl

Formally, `refl` is defined as `id0 = id0`, i.e. the empty graph equals itself, which always matches exactly once on any graph. If we drop the `by` clause, Chyp automatically assumes `by refl`, so the following is equivalent:

    rewrite foo :
      a * b ; c * d
      = (a ; c) * (b ; d)


The `def` statement introduced in the previous section is just syntactic sugar for a `gen` followed by a rule. That is:

    def a = g * h ; h * f

is equivalent to:

    gen a : 2 -> 2
    rule a_def : a = g * h ; h * f

Note that Chyp automatically figures out the arity and coarity for the new generator, since it has to match that of the given RHS.


## Automatically rewriting terms

Usually it is not very convenient to manually type in the results of rewriting a term. Chyp's solution for this is to introduce "holes", which you can then ask the rewriter to fill. For example, try typing this:

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


# Modules and importing

As structures and proofs get more complicated, we may want to split them into multiple files. Every chyp file defines a module, which can be imported in other chyp files. Suppose for example we define the following file `monoid.chyp`:

    gen m : 2 -> 1
    gen u : 0 -> 1
    rule assoc : m * id ; m = id * m ; m
    rule unitL : u * id ; m = id
    rule unitR : id * u ; m = id

If we want to define commutative monoids, we could start a new file `cmonoid.chyp` in the same directory and write:

    import monoid
    rule comm : sw ; m = m

By default, this loads all of the generators and rules from the first file into the second one. We may not want this, if there is some possibility that the symbols in one file will clash with the symbols in another. We can give a module its own namespace by adding `as ...` to the import statement:

    import monoid as M   # m is now M.m, u is M.u, assoc is M.assoc, etc.

This is especially important if we want to have multiple copies of the same structure. For example, we could start defining commutative semirings in a third file, `csemiring.chyp`:

    import cmonoid as M1
    import cmonoid as M2

    gen cp : 1 -> 2
    rule dist :
      M1.m * id ; M2.m = 
      = id * M1.m ; M2.m = cp * id * id ; id * sw * id ; M2.m * M2.m ; M1.m

You can also alias generators in imported modules as follows:

    gen m1 : 2 -> 1
    gen u1 : 0 -> 1
    gen m2 : 2 -> 1
    gen u2 : 0 -> 1
    import cmonoid as M1(m = m1, u = u1)
    import cmonoid as M2(m = m2, u = u2)

    gen cp : 1 -> 2
    rule dist :
      m1 * id ; m2 = 
      = id * m1 ; m2 = cp * id * id ; id * sw * id ; m2 * m2 ; m1

Even though we now have short aliases for generators, the rules still live in their respective namespaces. For example, `M1.assoc` can be used to rewrite `m1 * id ; m1` to `id * m1 ; m1` and `M2.assoc` will rewrite `m2 * id ; m2` to `id * m2 ; m2`.

This is especially convenient if modules share generators in non-trivial ways. For example, a pair of Frobenius algebras interacting as a bialgebra could be defined this way, assuming `frobenius.chyp` and `bialg.chyp` have already been defined:

    gen m1 : 2 -> 1
    gen u1 : 0 -> 1
    gen n1 : 1 -> 2
    gen v1 : 1 -> 0

    gen m2 : 2 -> 1
    gen u2 : 0 -> 1
    gen n2 : 1 -> 2
    gen v2 : 1 -> 0

    import frobenius as F1(m = m1, u = u1, n = n1, v = v1)
    import frobenius as F2(m = m2, u = u2, n = n2, v = v2)
    import bialg as B1(m = m1, u = u1, n = n2, v = v2)
    import bialg as B2(m = m2, u = u2, n = n1, v = v1)

We can even set the generators in an imported module equal to arbitrary terms, as long as the types match.

To understand how this works, it is useful to know that this is just some syntactic sugar that takes advantage of the behaviour of the `gen` statement. Normally, the `gen` statement will add a new generator to the current namespace. However, if a term with that name already exists, it will simply check the already existing term has the right arity and coarity. This allows us to alias generators in a module using `let` statements _before_ it is imported. So, in fact, the line:

    import frobenius as F1(m = m1, u = u1, n = n1, v = v1)

is exactly equivalent to:

    let F1.m = m1
    let F1.u = u1
    let F1.n = n1
    let F1.v = v1
    import frobenius as F1

Whenever an `m` is encountered in `frobenius.chyp` (which will be interpreted as `F1.m`), it will automatically get replaced by `m1` thanks to the `let` statement.

If we alias generators to some more complicated terms, these just end up the RHS of the `let` statements. For example, we could get the "almost" Frobenius algebra laws of the [ZW calculus](https://arxiv.org/abs/1501.07082) with a statement like this:


    gen m : 2 -> 1
    gen u : 0 -> 1
    gen n : 1 -> 2
    gen v : 1 -> 0
    gen d : 1 -> 1

    import frobenius as W(m = d * d ; m, u = u, n = d ; n, v = d ; v)

where the last line is equivalent to:

    let W.m = d * d ; m
    let W.u = u
    let W.n = d ; n
    let W.v = d ; v
    import frobenius as W


## Finding modules

The `import` statement always looks for `*.chyp` files in the same directory of the current file. Chyp doesn't have a notion of "search paths" for modules, but this might be added in the future.

Files can be imported from subdirectories by adding dots:

    import algebra.frobenius  # imports algebra/frobenius.chyp

You can go to a file being imported by placing the cursor on the import statement and pressing `CTRL+G`.

