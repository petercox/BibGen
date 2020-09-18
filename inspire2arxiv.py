#!/usr/bin/python3

"""inspire2arxiv.py: Converts all references in a tex file from Inspire texkey to arXiv reference (where possible) to avoid duplicate entries in the bibliography.

usage: inspire2arxiv.py <bibfile>
"""

__author__ = "Peter Cox"
__version__ = '1.1'
__date__ = '19-09-2020'


import os.path, sys

if len(sys.argv) < 2:
    print 'usage: convert_refs.py <bibfile>'
    sys.exit(-1)

bibfile = sys.argv[1]

# Check for valid bibfile
if not bibfile.endswith('bib') or not os.path.exists(bibfile):
    print("'%s' is not a valid bibfile.")%bibfile
    sys.exit(1)

id_dict = {}
inspire_id = None

# Read bibfile
with open(bibfile) as f:
    for line in f:
        line = line.strip()
        
        # Get inspire texkey
        if line.startswith('@'):
            inspire_id = line.split('{')[1].split(',')[0]

        # Get arXiv reference
        if line.startswith('eprint'):
            arxiv_id = line.split('"')[1]
            if len(arxiv_id) > 20:
                continue
            if inspire_id is not None and inspire_id != arxiv_id:
                id_dict[inspire_id] = arxiv_id
                inspire_id = None

print(id_dict)

texfile = sys.argv[1].split('.bib')[0] + '.tex'

# Check whether to overwrite
ans = raw_input('Warning this will overwrite existing tex file. Do you want to continue? (y/n): ')
while ans != 'y' and ans != 'n':
    ans = raw_input("Please answer y or n: ")
        
    if ans == 'n':
        sys.exit()  

# Read texfile and update tex
newtex = []
with open(texfile) as f:
    for line in f:
        refs = []

        # Get references in line
        for cite in line.split('\cite{')[1:]:
            refs += cite.split('}', 1)[0].split(',')

        # Replace inspire texkey with arXiv reference
        for ref in refs:
            try:
                line = line.replace(ref,id_dict[ref])
            except KeyError:
                pass
        
        newtex.append(line)

# Update texfile
with open(texfile, 'w') as f:
    for line in newtex:
        f.write(line)
