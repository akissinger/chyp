# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
from pygments.lexer import RegexLexer
from pygments import token
from sphinx.highlighting import lexers

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Chyp'
copyright = '2024, Aleks Kissinger'
author = 'Aleks Kissinger'
release = '0.6'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['autoapi.extension', 'sphinx_rtd_theme', 'sphinx.ext.napoleon']
autoapi_dirs = ['../chyp']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']


# -- Chyp syntax highlighting -------------------------------------------------
class ChypLexer(RegexLexer):
    name = 'chyp'
    tokens = {
        'root': [
            (r'#.*$', token.Comment),
            (r'"(\\\\|\\"|[^"])*"', token.String),
            (r'theorem', token.Keyword),
            (r'rule', token.Keyword),
            (r'gen', token.Keyword),
            (r'rewrite', token.Keyword),
            (r'proof', token.Keyword),
            (r'qed', token.Keyword),
            (r'by', token.Keyword),
            (r'apply', token.Keyword),
            (r'[a-zA-Z_\\.]', token.Name),
            (r'[*=;]', token.Operator),
            (r'[:(),]', token.Punctuation),
            (r'->', token.Operator),
            (r'[0-9]', token.Number),
            (r'\s', token.Text)
        ]
    }

lexers['chyp'] = ChypLexer()
