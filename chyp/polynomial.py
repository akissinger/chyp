from collections import defaultdict, Counter
from itertools import zip_longest
from IPython.display import Math

class Polynomial:
    def __init__(self, terms=None, subs=None):

        self.terms = Counter()
        
        for exps, coeff in terms:
            if coeff != 0:
                e = self._normalize_exponents(exps)
                self.terms[e] += coeff
        
        self.nvars = len(max(self.terms.keys(), 
                             key=lambda x: len(x),
                             default=tuple()))

        if subs is not None and len(subs) != self.nvars:
            raise ValueError('Must substitute all variables!')

        self.subs = subs
    
    def _normalize_exponents(self, exponents):
        """Normalize the exponents by removing trailing zeros."""
        if len(exponents) == 1:
            return exponents
        
        while exponents and exponents[-1] == 0:
            exponents = exponents[:-1]
        return exponents
    
    def __str__(self):
        """Pretty-print the polynomial."""
        if not self.terms:
            return "0"
        
        result = []
        for exponents, coeff in sorted(self.terms.items(), key=lambda x: x[0]):
            term = [f"{coeff}"]
            for i, exp in enumerate(exponents):
                if exp != 0:
                    term.append(f"x{i+1}^{exp}")
            result.append("".join(term))

        return " + ".join(result).replace("+ -", "- ")
    
    def latex(self, subs=None):
        """Return LaTeX representation of the polynomial."""
        if not self.terms:
            return "$0$"

        # Try to see if we have subs stored previously
        # This is mainly a convinience when parsing
        # but we want to still allow overwriting
        if subs is None:
            subs = self.subs

        if subs is not None and len(subs) != self.nvars:
            raise ValueError('Must substitute all variables!')
        
        terms = []
        for exponents, coeff in sorted(self.terms.items(), key=lambda x: x[0]):
            term = []

            # Add coefficient, skip for 1 or -1 unless it's a constant term
            if coeff == -1 and any(exp != 0 for exp in exponents):
                term.append("-")
            elif coeff != 1 or all(exp == 0 for exp in exponents):
                term.append(f"{coeff}")
            
            # Add variables with exponents
            for i, exp in enumerate(exponents):

                var = subs[i] if subs else f'x_{i}'
                if exp == 1:
                    term.append(var)
                elif exp != 0:
                    term.append(f"{var}^{{{exp}}}")
                    
            if not term:
                term.append("1")  # In case of constant term '1'

            terms.append("".join(term))


        res = f'${" + ".join(terms)}$'

        # If we ended up with + (-x) turn it into - x 
        res = res.replace("+ -", "- ")
        
        return res
    
    def __eq__(self, other):
        return self.terms == other.terms
    
    def __add__(self, other):
        res = self.terms + other.terms
        return Polynomial(res)

    def __sub__(self, other):
        res = self.terms - other.terms
        return Polynomial(res)
    
    def __mul__(self, other):
        res = Counter()
        
        for exp1, coeff1 in self.terms.items():
            for exp2, coeff2 in other.terms.items():
                new_exp = tuple(e1 + e2 for e1, e2 in zip_longest(exp1, exp2, fillvalue=0))
                res[new_exp] += coeff1 * coeff2
            
        return Polynomial(res)

    
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

def show(*args):

    for p in args:
        display(Math(p.latex()))
