"""The license and attribution that travel with the printable files (STL headers, the LICENSE.txt in every zip)."""
URL = 'https://github.com/scottbez1/FaderBuddy'
DEED = 'https://creativecommons.org/licenses/by-sa/4.0/'
CREDIT = 'FaderDeck, from the FaderBuddy open-source project (github.com/scottbez1/FaderBuddy)'

def stl_header(part):
    """The 80-byte binary STL header: slicers ignore it, but it carries the attribution with every part. It must not start with
    'solid' (some readers would take the file for ASCII STL)."""
    h = f'FaderDeck {part} | github.com/scottbez1/FaderBuddy | CC BY-SA 4.0'
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
