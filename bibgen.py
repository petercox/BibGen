#!/usr/bin/python3

##################################################
"""bibgen.py: Script to automatically generate .bib files.

usage: bibgen.py <TeXfile> (options)

Parses a tex file for \cite commands and dowloads citation information from Inspire using the API.
Works with arXiv preprint number, Inspire TeXkey or DOI.

The tex file is also updated to ensure the same identifier is used in each \cite command and avoid duplicate bibliography entries.

The default behaviour is to append new references to an existing bib file. This can be changed using the --overwrite option.

References not available on Inspire can be included in the output by placing them in the file noinspire.bib.

Copyright 2020 Peter Cox
"""

__author__ = "Peter Cox"
__email__ = "peter.cox@unimelb.edu.au"
__version__ = "2.3"

##################################################

import argparse, os.path, re, sys, urllib.request


# Citation identifier types
arxivRE = re.compile(r'^\d{4}.\d{4,5}$')
arxiv_oldRE = re.compile(r'^[a-z.\-]+/[09]\d{6}$', re.IGNORECASE)
inspireRE = re.compile(r'^[a-zA-Z\-]+:\d{4}[a-z]{2,3}$')
doiRE = re.compile(r'^10.[0-9.]{4,}/\w+')

##################################################

def ChangeBibKey(bibtex, newkey):
    """Replace the bibtex key with newkey."""

    bibdata = bibtex.split('{', 1)
    ref_type = bibdata[0]
    ref_details = bibdata[1].split(',',1)[1]        
    return '%s{%s,%s'%(ref_type, newkey, ref_details)

##################################################

def ReadBibtex(bibfile):
    """Read bibtex data from file and store as dictionary of references."""
    
    refs = {}
    key = None

    with open(bibfile) as f:
        for line in f:
            if line.startswith('@'):
                if key is not None:
                    refs[key] = data
                key = line.split('{',1)[1].rsplit(',',1)[0]
                data = ''
            if key is not None:
                data += line
        if key is not None:
            refs[key] = data

    return refs

##################################################

def RefsFromBib(bibfile):
    """Read references from bib file."""

    bibRefs = []
    with open(bibfile) as f:
        for line in f:
            if line.startswith('@'):
                bibRefs.append(line.split('{',1)[1].rsplit(',')[0])

    return bibRefs

##################################################

def RefsFromTex(texfile):
    """Read references from tex file."""

    texRefs = []
    with open(texfile) as f:
        for line in f:
            if line.startswith('%'):
                continue
            for cite in line.split('\cite{')[1:]:
                refs = cite.split('}', 1)[0].split(',')

                for ref in refs:
                    ref = ref.strip()
                    if ref != '':
                        texRefs.append(ref)

    # Remove duplicates
    texRefs = list(dict.fromkeys(texRefs))

    return texRefs

##################################################

def GetIdentifiers(bibtex):
    """Retrieve TeXkey, eprint and DOI from bibtex."""

    inspire_id = None
    arxiv_id = None
    doi = None
    IDs = {'arxiv': None, 'inspire': None, 'doi': None}

    for line in bibtex.splitlines():
        line = line.strip()

        # Get Inspire TeXkey
        if line.startswith('@'):
            inspire_id = line.split('{')[1].split(',')[0]
            if inspireRE.match(inspire_id) is not None:
                IDs['inspire'] = inspire_id

        # Get arXiv identifier
        elif line.startswith('eprint'):
            arxiv_id = line.split('"')[1]
            if arxivRE.match(arxiv_id) is not None or arxiv_oldRE.match(arxiv_id) is not None:
                IDs['arxiv'] = arxiv_id

        # Get DOI
        elif line.startswith('doi'):
            doi = line.split('"')[1]
            if doiRE.match(doi) is not None:
                IDs['doi'] = doi

    return IDs

##################################################

def GetInspireBibtex(ref):
    """Get bibtex information using Inspire API.
    
    Works with arXiv identifier, Inspire TeXkey, or DOI.
    """

    # Determine citation type
    if arxivRE.match(ref) is not None or arxiv_oldRE.match(ref) is not None:
        identifier = 'arxiv'
    elif inspireRE.match(ref) is not None:
        identifier = 'texkey'
    elif doiRE.match(ref) is not None:
        identifier = 'doi'
    else:
        return None

    # Retrieve bibtex data using Inspire API
    try:
        if identifier == 'texkey':
            bibtex = urllib.request.urlopen('https://inspirehep.net/api/literature?q=texkey:{}&format=bibtex'.format(ref)).read()
        else:
            bibtex = urllib.request.urlopen('https://inspirehep.net/api/{}/{}?format=bibtex'.format(identifier,ref)).read()
    except urllib.error.HTTPError:
        return None

    bibtex = bibtex.decode()
    try:
        bibtex.split('@',1)[1].rsplit('}\n',2)[0]
    except IndexError:
        return None
        
    return bibtex

##################################################

def UpdateTeXCite(texfile, replacements):
    """Replace duplicate cite commands with common identifier according to dictionary of replacements."""

    # Read texfile and update tex
    newtex = []
    with open(texfile) as f:
        for line in f:
            refs = []

            # Get references in line
            for cite in line.split('\cite{')[1:]:
                refs += cite.split('}', 1)[0].split(',')

            # Replace inspire TeXkey with arXiv identifier
            for ref in refs:
                try:
                    line = line.replace(ref,replacements[ref])
                except KeyError:
                    pass
        
            newtex.append(line)

    # Update texfile
    with open(texfile, 'w') as f:
        for line in newtex:
            f.write(line)
        pass

##################################################

def main():
    """Automatically generate bib file from tex file using Inspire API."""

    # Parse options
    parser = argparse.ArgumentParser(description='Automatically generate bib file from tex file using Inspire API.')
    parser.add_argument('texfile')

    parser.add_argument('--bibfile', dest='bibfile', default=None, help='Specify name of bib file')
    parser.add_argument('--overwrite', dest='overwrite', action='store_true', default=False, help='Overwrite bib file')

    args = parser.parse_args()

    texfile = args.texfile

    base = texfile.rsplit('tex', 1)
    if len(base) == 1:
        print('Error: {} is not a valid .tex file.'.format(texfile))
        sys.exit(1)
    
    if args.bibfile is not None:
        bibfile = args.bibfile
    else:
        bibfile = base[0] + 'bib' 

    if args.overwrite == True and os.path.exists(bibfile):
        ans = input('Warning this will overwrite existing bib file. Do you want to continue? (y/n): ')
        while ans != 'y' and ans != 'n':
            ans = input("Please answer y or n: ")
        
        if ans == 'n':
            sys.exit()

    # Read citations from existing bib file if updating
    bibRefs = {}
    if not args.overwrite:
        if os.path.exists(bibfile):
            bibRefs = RefsFromBib(bibfile)
        else:
            args.overwrite = True

    # Read citations from tex file
    texRefs = RefsFromTex(texfile)
    print('Found %d references.'%len(texRefs))

    # Check for noinspire bib file and read bibtex
    if os.path.exists('noinspire.bib'):
        noinspireRefs = ReadBibtex('noinspire.bib')
    else:
        noinspireRefs = {}

    # Download citation data from Inspire 
    writeRefs = []
    texRepl = {}
    for ref in texRefs:
        
        # Don't download data if it already exists in bib file
        if (not args.overwrite) and ref in bibRefs:
            continue

        bibtex = GetInspireBibtex(ref)

        # Ensure only a single identifier is used
        # Preference is arXiv > Inspire > DOI
        if bibtex is not None:
            ids = GetIdentifiers(bibtex)

            if ids['arxiv'] in texRefs:
                writekey = ids['arxiv']

                if ids['inspire'] in texRefs:
                    texRepl[ids['inspire']] = ids['arxiv']
                if ids['doi'] in texRefs:
                    texRepl[ids['doi']] = ids['arxiv']

            elif ids['inspire'] in texRefs:
                writekey = ids['inspire']

                if ids['doi'] in texRefs:
                    texRepl[ids['doi']] = ids['inspire']

            else:
                writekey = ids['doi']

            if not writekey in bibRefs:
                writeRefs.append(ChangeBibKey(bibtex, writekey))

            # Remove duplicate references from texRefs
            for i in ids.values():
                if i != ref:
                    try:
                        texRefs.remove(i)
                    except:
                        ValueError

        # If reference can't be found on Inspire check noinspire.bib references
        else:
            try:
                writeRefs.append(noinspireRefs[ref])
            except KeyError:
                print('Could not find reference for {}. Skipping.'.format(ref))
            else:
                print('Could not find inspire reference for {}. Using noinspire.bib entry.'.format(ref))
            continue

    # Write bib file
    if args.overwrite:
        mode = 'w'
    else:
        mode = 'a'

    with open(bibfile, mode) as f:
        for bibtex in writeRefs:
            f.write(bibtex+'\n')

    # Update tex file to remove duplicate refs if required
    if len(texRepl) > 0:
        print('TeX file contains identical references with different identifiers.')
        ans = input('Do you want to update the \cite commands in the tex file? (order of preference is arXiv > Inspire > DOI) (y/n): ')
        while ans != 'y' and ans != 'n':
            ans = input("Please answer y or n: ")
        
        if ans == 'n':
            sys.exit()  

        UpdateTeXCite(texfile, texRepl)

##################################################

if __name__ == '__main__':
    main()

##################################################
