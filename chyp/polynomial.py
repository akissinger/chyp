class MPolynomial:
    def __init__(self, terms=None, vars=None):
        """
        Initialize a sparse multivariate polynomial.
        
        args:
            terms: A list of tuples (coefficient, powers_dict), where:
                - coefficient is a number (int/float).
                - powers_dict is a dictionary representing the powers of each variable in `variables`, 
                  with variable indices as keys and exponents as values.
            variables: A list of variable names, e.g., ["x", "y", "z"].
        """
        self.variables = vars if vars else []
        self.terms = {}  # Dictionary to store terms as {powers_dict: coefficient}

        if terms:
            for coeff, powers in terms:
                self.add_term(coeff, powers)

    def add_term(self, coeff, powers):
        """
        Add a term with a coefficient and a dictionary of powers to the polynomial.
        
        Args:
            coeff: The coefficient of the term (e.g., 3).
            powers: A dictionary representing the powers of variables (e.g., {0: 2, 1: 1} for x^2*y).
        """
        # If coefficient is zero, we do not add the term
        if coeff == 0:
            return
        
        # Convert powers to an immutable form (frozenset) for use as a dictionary key
        powers = frozenset(powers.items())
        if powers in self.terms:
            self.terms[powers] += coeff
            # Remove if the coefficient becomes zero
            if self.terms[powers] == 0:
                del self.terms[powers]
        else:
            self.terms[powers] = coeff

    def __repr__(self):
        """
        Return a human-readable string representation of the polynomial.
        """
        if not self.terms:
            return "0"
        
        result = []
        for powers, coeff in sorted(self.terms.items(), key=lambda x: x[1], reverse=True):
            term_str = str(coeff)
            for var_idx, power in dict(powers).items():
                var_name = self.variables[var_idx]
                if power == 1:
                    term_str += f"*{var_name}"
                elif power > 1:
                    term_str += f"*{var_name}^{power}"
            result.append(term_str)
        
        return " + ".join(result).replace("+-", "- ")

    def __add__(self, other):
        """
        Add two multivariable polynomials and return a new polynomial.
        """
        result = MPolynomial(vars=self.variables)
        # Add terms from both polynomials
        for powers, coeff in self.terms.items():
            result.add_term(coeff, dict(powers))
        for powers, coeff in other.terms.items():
            result.add_term(coeff, dict(powers))
        return result

    def __mul__(self, other):
        """
        Multiply two polynomials and return the result.
        """
        result = MPolynomial(vars=self.variables)
        for powers1, coeff1 in self.terms.items():
            for powers2, coeff2 in other.terms.items():
                # Combine powers by adding the exponents for matching variables
                new_powers = dict(powers1)
                for var_idx, power2 in dict(powers2).items():
                    if var_idx in new_powers:
                        new_powers[var_idx] += power2
                    else:
                        new_powers[var_idx] = power2
                result.add_term(coeff1 * coeff2, new_powers)
        return result

    def eval(self, **values):
        """
        Evaluate the polynomial for given variable values.
        
        Args:
            values: A dictionary mapping variable names to their values.
        
        Returns:
            The result of the polynomial evaluation.
        """
        result = 0
        for powers, coeff in self.terms.items():
            term_value = coeff
            for var_idx, power in dict(powers).items():
                var_name = self.variables[var_idx]
                if var_name in values:
                    term_value *= values[var_name] ** power
                else:
                    raise ValueError(f"Value for variable '{var_name}' is not provided.")
            result += term_value
        return result

# Example usage:

# # Polynomial: 2*x^2*y + 3*x*y^2 + 5
p1 = MPolynomial([
    (2, {0: 2, 1: 2}),  # 2*x
    (3, {0: 1}),  # 3
    ],
    vars = ['x', 'y'])


3*x + 2*x^2*y^2
print(p1.eval(x=2, y=1)) 



# # Polynomial: x^3 + 4*x*y
# p2 = MPolynomial([
#     (1, {0: 3}),        # x^3
# ], vars = ['y'])


# print(p1)
# print(p2)
# # Adding polynomials
# p3 = p1 + p2
# print("p3:", p3)  # Output: 2*x^2*y + 3*x*y^2 + x^3 + 4*x*y + 5

# # Multiplying polynomials
# p4 = p1 * p2
# print("p4:", p4)  # Output: 2*x^5*y + 8*x^3*y^2 + 3*x^4*y^2 + 5*x^3 + 20*x*y + 5

# # Evaluating the polynomial
# values = {"x": 2, "y": 3}
# result = p3.eval(values)
# print(f"p3({values}) =", result)  # Output: p3({'x': 2, 'y': 3}) = 147













# class MPolynomial:
#     def __init__(self, terms, variables=None):
#         """
#         Initialize the polynomial with a list of terms.
#         Each term is represented as a tuple: (coefficient, {var_index: exponent}).
#         variables: Optional list of variable names. Defaults to x_1, x_2, etc.
#         """
#         self.terms = self._simplify(terms)
#         # Use provided variable names or default to x_1, x_2, ...
#         num_vars = max((max(term[1].keys(), default=-1) for term in terms), default=0) + 1
#         self.variables = variables if variables else [f"x_{i+1}" for i in range(num_vars)]

#     def _simplify(self, terms):
#         """
#         Combine terms with the same exponents by summing their coefficients.
#         Remove terms with zero coefficients.
#         """
#         term_dict = {}
#         for coeff, exponents in terms:
#             exponents = frozenset(exponents.items())  # Use frozenset for dict-like keys
#             if exponents in term_dict:
#                 term_dict[exponents] += coeff
#             else:
#                 term_dict[exponents] = coeff

#         # Remove terms with zero coefficients
#         simplified_terms = [(coeff, dict(exps)) for exps, coeff in term_dict.items() if coeff != 0]

#         # Sort terms for consistent ordering (optional, can be omitted)
#         return sorted(simplified_terms, key=lambda term: tuple(sorted(term[1].items())), reverse=True)

#     def __repr__(self):
#         def format_term(coeff, exps):
#             # Format the term based on variable names and sparse exponent dictionary
#             var_terms = [f"{self.variables[var]}^{exp}" if exp != 1 else f"{self.variables[var]}"
#                          for var, exp in exps.items()]
#             var_part = "*".join(var_terms)
#             return f"{coeff}" + (f"*{var_part}" if var_part else "")

#         return " + ".join(format_term(coeff, exps) for coeff, exps in self.terms)

#     def __eq__(self, other):
#         return self.terms == other.terms

#     def __add__(self, other):
#         combined_terms = self.terms + other.terms
#         return MPolynomial(combined_terms, self.variables)

#     def __mul__(self, other):
#         """
#         Multiply two multivariable polynomials.
#         Multiply each term from the first polynomial with each term from the second polynomial.
#         """
#         result_terms = []
#         for coeff1, exps1 in self.terms:
#             for coeff2, exps2 in other.terms:
#                 # Multiply coefficients
#                 new_coeff = coeff1 * coeff2
#                 # Add exponents for each variable
#                 new_exps = exps1.copy()  # Start with exponents from the first term
#                 for var, exp in exps2.items():
#                     new_exps[var] = new_exps.get(var, 0) + exp
#                 result_terms.append((new_coeff, new_exps))

#         return MPolynomial(result_terms, self.variables)

#     def evaluate(self, **values):
#         """
#         Evaluate the polynomial by substituting values for each variable.
#         values: Dictionary where the keys are variable names or default names.
#         Example: p.evaluate(x=1, y=2) or p.evaluate(x_1=1, x_2=2)
#         """
#         result = 0
#         for coeff, exps in self.terms:
#             term_value = coeff
#             for var, exp in exps.items():
#                 var_name = self.variables[var]
#                 var_value = values.get(var_name, 0)
#                 term_value *= var_value ** exp
#             result += term_value
#         return result


# # # Example usage
# # p1 = MPolynomial([(2, {0: 2, 1: 1}), (3, {0: 1, 1: 2}), (5, {})], variables=["x", "y"])  
# # # 2*x^2*y + 3*x*y^2 + 5
# # p2 = MPolynomial([(4, {0: 1, 1: 2}), (3, {0: 2, 1: 1})], variables=["x", "y"])               
# # # 4*x*y^2 + 3*x^2*y

# # print("p1:", p1)
# # print("p2:", p2)

# # # Addition of two multivariable polynomials
# # p3 = p1 + p2  # Should represent 5*x^2*y + 7*x*y^2 + 5
# # print("p1 + p2:", p3)

# # # Multiplication of two multivariable polynomials
# # p4 = p1 * p2
# # print("p1 * p2:", p4)

# # # Evaluate polynomial at x=1, y=2
# # evaluation = p1.evaluate(x=1, y=2)
# # print("p1 evaluated at x=1, y=2:", evaluation)

# # # Use default variable names (x_1, x_2)
# # p5 = MPolynomial([(2, {0: 1}), (1, {1: 1})])  # 2*x_1 + x_2
# # print("p5:", p5)

# # # Evaluate using default names
# # evaluation_default = p5.evaluate(x_1=1, x_2=2)
# # print("p5 evaluated at x_1=1, x_2=2:", evaluation_default)
