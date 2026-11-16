"""The license, attribution and design version that travel with the printable files (STL headers, the LICENSE.txt in every
zip)."""
import os
URL = 'https://github.com/scottbez1/FaderBuddy'
DEED = 'https://creativecommons.org/licenses/by-sa/4.0/'
CREDIT = 'FaderDeck, from the FaderBuddy open-source project (github.com/scottbez1/FaderBuddy)'
VERSION = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'VERSION')).read().strip()   # see CHANGELOG.md

def stl_header(part, version=None):
    """The 80-byte binary STL header: slicers ignore it, but it carries the attribution with every part. It must not start with
    'solid' (some readers would take the file for ASCII STL)."""
    h = f'FaderDeck {"v" + version + " " if version else ""}{part} | github.com/scottbez1/FaderBuddy | CC BY-SA 4.0'
    assert len(h) <= 80 and not h.startswith('solid'), h
    return h

def text(title, files):
    return f'''{title}

From the FaderBuddy open-source project: {URL}

These files are licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0):
{DEED}

You may share and adapt them, including commercially, as long as you
- give credit: "{CREDIT}", link the license, and say whether you changed anything;
- release anything you make from them under the same license, CC BY-SA 4.0.

Files:
''' + ''.join(f'- {f}\n' for f in files)
