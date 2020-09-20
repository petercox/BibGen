#!/usr/bin/python3

##################################################
"""cite2arxiv.py: Converts all \cite commands in a tex file to arXiv identifier (where possible).

usage: cite2arxiv.py <texfile> <bibfile>

Copyright 2020 Peter Cox
"""
##################################################

import os.path, re, sys
from bibgen import UpdateTeXCite

if len(sys.argv) < 3:
    print('usage: inspire2arxiv.py <texfile> <bibfile>')
    sys.exit(-1)

texfile = sys.argv[1]
bibfile = sys.argv[2]

# Check for valid files
if not texfile.endswith('tex') or not os.path.exists(texfile):
    print("'%s' is not a valid tex file."%texfile)
    sys.exit(1)
if not bibfile.endswith('bib') or not os.path.exists(bibfile):
    print("'%s' is not a valid bib file."%bibfile)
    sys.exit(1)


arxivRE = re.compile(r'^\d{4}.\d{4,5}$')
arxiv_oldRE = re.compile(r'^[a-z.\-]+/[09]\d{6}$', re.IGNORECASE)

replacements = {}
refID = None

# Read bibfile to get dictionary of replacements
with open(bibfile) as f:
    for line in f:
        line = line.strip()
        
        # Get reference key
        if line.startswith('@'):
            refID = line.split('{')[1].split(',')[0]

        # Get arXiv reference
        elif line.startswith('eprint'):
            arxivID = line.split('"')[1]
            if refID is not None and refID != arxivID:
                if arxivRE.match(arxivID) is not None or arxiv_oldRE.match(arxivID) is not None:
                    replacements[refID] = arxivID
                    refID = None

print(replacements)

if len(replacements) == 0:
    sys.exit()

# Check whether to overwrite
ans = input('Warning this will overwrite existing tex file. Do you want to continue? (y/n): ')
while ans != 'y' and ans != 'n':
    ans = input("Please answer y or n: ")
        
    if ans == 'n':
        sys.exit()  

UpdateTeXCite(texfile, replacements)

##################################################
