#     chyp - An interactive theorem prover for string diagrams 
#     Copyright (C) 2022 - Aleks Kissinger
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Dict
from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

PALETTES: Dict[str, Dict[str,str]] = dict()

PALETTES['catppuccin_macchiato'] = {
    'rosewater': '#f4dbd6',
    'flamingo':  '#f0c6c6',
    'pink':      '#f5bde6',
    'mauve':     '#c6a0f6',
    'red':       '#ed8796',
    'maroon':    '#ee99a0',
    'peach':     '#f5a97f',
    'yellow':    '#eed49f',
    'green':     '#a6da95',
    'teal':      '#8bd5ca',
    'sky':       '#91d7e3',
    'sapphire':  '#7dc4e4',
    'blue':      '#8aadf4',
    'lavender':  '#b7bdf8',
    'text':      '#cad3f5',
    'subtext1':  '#b8c0e0',
    'subtext0':  '#a5adcb',
    'overlay2':  '#939ab7',
    'overlay1':  '#8087a2',
    'overlay0':  '#6e738d',
    'surface2':  '#5b6078',
    'surface1':  '#494d64',
    'surface0':  '#363a4f',
    'base':      '#24273a',
    'mantle':    '#1e2030',
    'crust':     '#181926',

    'green_bg':  '#36504f', # non-standard
    'red_bg':    '#863a4f', # non-standard
}

PALETTES['catppuccin_latte'] = {
    'rosewater': '#dc8a78',
    'flamingo':  '#dd7878',
    'pink':      '#ea76cb',
    'mauve':     '#8839ef',
    'red':       '#d20f39',
    'maroon':    '#e64553',
    'peach':     '#fe640b',
    'yellow':    '#df8e1d',
    'green':     '#40a02b',
    'teal':      '#179299',
    'sky':       '#04a5e5',
    'sapphire':  '#209fb5',
    'blue':      '#1e66f5',
    'lavender':  '#7287fd',
    'text':      '#4c4f69',
    'subtext1':  '#5c5f77',
    'subtext0':  '#6c6f85',
    'overlay2':  '#7c7f93',
    'overlay1':  '#8c8fa1',
    'overlay0':  '#9ca0b0',
    'surface2':  '#acb0be',
    'surface1':  '#bcc0cc',
    'surface0':  '#ccd0da',
    'base':      '#eff1f5',
    'mantle':    '#e6e9ef',
    'crust':     '#dce0e8',

    'green_bg':  '#bbffcc', # non-standard
    'red_bg':    '#ff9999', # non-standard
}

THEMES: Dict[str, Dict[str,str]] = dict()
for t in ('catppuccin_macchiato', 'catppuccin_latte'):
    THEMES[t] = {
      'bg': PALETTES[t]['base'],
      'fg': PALETTES[t]['text'],
      'fg_bright': PALETTES[t]['lavender'],
      'bg_good': PALETTES[t]['green_bg'],
      'bg_bad': PALETTES[t]['red_bg'],
      'bg_alt': PALETTES[t]['crust'],
      'bg_button': PALETTES[t]['mantle'],
      'fg_button': PALETTES[t]['text'],
      'fg_link': PALETTES[t]['blue'],
      'bg_highlight': PALETTES[t]['blue'],
      'fg_highlight': PALETTES[t]['crust'],

      'bg_sel': PALETTES[t]['surface0'], 
      'fg_keyword': PALETTES[t]['blue'],
      'fg_ident': PALETTES[t]['sky'], 
      'fg_num': PALETTES[t]['red'],
      'fg_op': PALETTES[t]['yellow'],
      'fg_comment': PALETTES[t]['overlay1'],
      'fg_string': PALETTES[t]['green']
    }

def current_theme() -> Dict[str,str]:
    conf = QSettings('chyp', 'chyp')

    theme_name = conf.value('theme')
    if not theme_name or not isinstance(theme_name, str):
        theme_name = 'catppuccin_macchiato'

    return THEMES[theme_name]

def apply_theme() -> None:
    theme = current_theme()

    QApplication.setStyle("Fusion")
    # Now use a palette to switch to theme colors:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(theme['bg']))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(theme['fg']))
    palette.setColor(QPalette.ColorRole.Base, QColor(theme['bg']))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme['bg_alt']))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(theme['fg']))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(theme['fg']))
    palette.setColor(QPalette.ColorRole.Text, QColor(theme['fg']))
    palette.setColor(QPalette.ColorRole.Button, QColor(theme['bg_button']))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme['fg_button']))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(theme['fg_bright']))
    palette.setColor(QPalette.ColorRole.Link, QColor(theme['fg_link']))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(theme['bg_highlight']))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(theme['fg_highlight']))
    QApplication.setPalette(palette)
