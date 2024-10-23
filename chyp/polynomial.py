from collections import defaultdict, Counter
from itertools import zip_longest, dropwhile
from IPython.display import Math
from functools import reduce


def const_poly(n: int):
    return Polynomial([
        ((0,), n)
    ])

class Polynomial:

    # Functions used by __str__ to output
    # normal str repr or latex
    default_str = (
        lambda: "0", # base case no terms
        lambda v, e: f"{v}^{e}",
        lambda terms: ' + '.join(terms)
    )

    latex_str = (
        lambda: "$0$", # base case no terms
        lambda v, e: f"{v}^{{{e}}}",
        lambda terms: f'${" + ".join(terms)}$'
    )
    
    def __init__(self, terms=None, subs=None,
                 str_repr=default_str):

        self.terms = Counter()
        self.str_repr = str_repr
        
        for exps, coeff in terms:
            if coeff != 0:
                e = self._normalize_exponents(exps)
                self.terms[e] += coeff
                
        max_term = max(self.terms.keys(), default=tuple(), key=lambda x: len(x))
        self.nvars = 0 if self.is_const() else len(max_term)

        if subs is not None and len(subs) != self.nvars:
            raise ValueError('Must substitute all variables!')

        self.subs = subs if subs is not None else []


    def is_const(self):
        monomials = list(self.terms.keys())
        if len(monomials) == 1 and monomials[0] == (0,):
            return True

        return False
    
    def _normalize_exponents(self, exponents):
        """Normalize the exponents by removing trailing zeros."""
        if len(exponents) == 1:
            return exponents
        
        while exponents and exponents[-1] == 0:
            exponents = exponents[:-1]
        return exponents
    
    # def __str__(self):
    #     """Pretty-print the polynomial."""
    #     if not self.terms:
    #         return "0"


    #     if self.subs is not None and len(self.subs) != self.nvars:
    #         raise ValueError('Must substitute all variables!')
        
    #     result = []
    #     for exponents, coeff in self.terms.items(), key=lambda x: x[0]:
    #         term = [f"{coeff}"]
    #         for i, exp in enumerate(exponents):
    #             if exp != 0:
    #                 var = self.subs[i] if self.subs else f'x_{i}'
    #                 term.append(f"{var}^{exp}")
    #         result.append("".join(term))

    #     s = " + ".join(result).replace("+ -", "- ")

    #     return s
        
        
    
    def __str__(self, subs=None):
        """
        Return str representation of the polynomial.
        Can be LaTeX or ascii
        """

        if not self.terms:
            return self.str_repr[0]()

        # Try to see if we have subs stored previously
        # This is mainly a convinience when parsing
        # but we want to still allow overwriting
        if subs is None:
            subs = self.subs

        if subs is not None and len(subs) != self.nvars:
            raise ValueError('Must substitute all variables!')
        
        terms = []
        for exponents, coeff in self.terms.items():
            term = []

            # Add coefficient, skip for 1 or -1 unless it's a constant term
            if coeff == -1 and any(exp != 0 for exp in exponents):
                term.append("-")
            elif coeff == 0:
                continue
            elif coeff != 1 or all(exp == 0 for exp in exponents):
                term.append(f"{coeff}")
            
            
            # Add variables with exponents
            for i, exp in enumerate(exponents):

                var = subs[i] if subs else f'x_{i}'
                if exp == 1:
                    term.append(var)
                elif exp != 0:
                    term.append(self.str_repr[1](var, exp))
                    
            if not term:
                term.append("1")  # In case of constant term '1'

            terms.append("".join(term))


        res = self.str_repr[2](terms)

        # If we ended up with + (-x) turn it into - x 
        res = res.replace("+ -", "- ")
        
        return res
    
    def __eq__(self, other): 
        terms = sorted(self.terms.items(), key=lambda x: x[1])
        other_terms = sorted(other.terms.items(), key=lambda x: x[1])

        for (e1, c1), (e2, c2) in zip_longest(terms, other_terms, fillvalue=((0,),0)):
            # Remove leading 0s
            e1 = tuple(dropwhile(lambda x: x == 0, e1))
            e2 = tuple(dropwhile(lambda x: x == 0, e2))

            if c1 != c2:
                return False
            
            if e1 != e2:
                return False
            
        return True
    
    def __add__(self, other):
        res = self.terms + other.terms
        return Polynomial(list(res.items()))

    def __sub__(self, other):
        res = self.terms - other.terms
        return Polynomial(list(res.items()))
    
    def __mul__(self, other):
        res = Counter()
        for exp1, coeff1 in self.terms.items():
            for exp2, coeff2 in other.terms.items():
                new_exp = tuple(e1 + e2 for e1, e2 in zip_longest(exp1, exp2, fillvalue=0))
                res[new_exp] += coeff1 * coeff2
            
        return Polynomial(list(res.items()))

    
    def eval(self, values):
        result = 0

        if len(values) != self.nvars: 
            raise ValueError(f'Provided {len(values)} values but the polynomial has {self.nvars} variables!')
        
        for exponents, coeff in self.terms.items():
            term_value = coeff
            for var, exp in zip(values, exponents):
                term_value *= var ** exp
            result += term_value
            
        return result


    def __call__(self, *args, **kwargs):
        return self.eval(args)

def show(*args):

    for p in args:
        display(Math(str(p)))
