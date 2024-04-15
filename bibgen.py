#!/usr/bin/python3

##################################################
"""bibgen.py: Script to automatically generate .bib files.

usage: bibgen.py <TeXfile> (options)

Parses a tex file and dowloads citation information from Inspire using 
the API. Works with \cite commands containing arXiv preprint number, 
Inspire ID or DOI.

The tex file is (optionally) updated to ensure the same identifier is 
used in each \cite command and avoid duplicate bibliography entries.

The default behaviour is to append new references to an existing bib file. 
This can be changed using the --overwrite option.

References not available on Inspire can be included in the output by 
placing them in the file noinspire.bib.

Copyright 2020 Peter Cox
"""

__author__ = "Peter Cox"
__email__ = "peter.cox@unimelb.edu.au"
__version__ = "3.0"

##################################################

import argparse, collections, os.path, sys, urllib.request

import bibentry

##################################################

def GetInspireBibTeX(ref):
    """Download BibTeX information using Inspire API.
    Works with arXiv identifier, Inspire TeXkey, or DOI.
    """

    # Determine citation type
    if bibentry.arxivRE.match(ref) is not None or bibentry.arxiv_oldRE.match(ref) is not None:
        identifier = 'arxiv'
    elif bibentry.inspireRE.match(ref) is not None:
        identifier = 'texkey'
    elif bibentry.doiRE.match(ref) is not None:
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

    # Check for valid bibtex
    try:
        bibtex.split('@',1)[1].rsplit('}\n',2)[0]
    except IndexError:
        return None
    
    return bibtex

##################################################

def ReadBibTeX(bibfile):
    """Read bibtex data from .bib file and store as 
    dictionary of BibEntry."""
    
    refs = collections.OrderedDict()
    tag = None

    with open(bibfile) as f:
        for line in f:

            if line.startswith('@'):
                if tag is not None:
                    refs[tag] = bibentry.BibEntry(bibtex)

                tag = line.split('{',1)[1].rsplit(',',1)[0]
                bibtex = ''

            if tag is not None:
                bibtex += line

        if tag is not None:
            refs[tag] = bibentry.BibEntry(bibtex)

    return refs

##################################################

def RefsFromBib(bibfile):
    """Read references IDs from .bib file."""

    bibRefs = []
    with open(bibfile) as f:
        for line in f:
            if line.startswith('@'):
                bibRefs.append(line.split('{',1)[1].rsplit(',')[0])

    return bibRefs

##################################################

def RefsFromTeX(texfile):
    """Read reference IDs from .tex file."""

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

def UpdateTeXCite(texfile, replacements):
    """Replace \cite IDs according to dictionary of replacements."""

    # Read texfile and update tex
    newtex = []
    with open(texfile) as f:
        for line in f:
            refs = []

            # Get references in line
            for cite in line.split('\cite{')[1:]:
                refs += cite.split('}', 1)[0].split(',')

            # Replace old identifier with new identifier
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

    parser.add_argument('-A', dest='arxiv', action='store_true', default=False, help='Replace all identifiers with arXiv ID')
    parser.add_argument('-D', dest='doi', action='store_true', default=False, help='Replace all identifiers with DOI')
    parser.add_argument('-I', dest='inspire', action='store_true', default=False, help='Replace all identifiers with Inspire ID')
    parser.add_argument('-v', dest='verbose', action='store_true', default=False, help='Verbose')

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

    # Issue warning before overwriting .bib file
    if args.overwrite == True and os.path.exists(bibfile):
        ans = input('Warning this will overwrite existing bib file. Do you want to continue? (y/n): ')
        while ans != 'y' and ans != 'n':
            ans = input("Please answer y or n: ")
        
        if ans == 'n':
            sys.exit()

    # Read bibtex from existing .bib file if updating and store in bibRefs
    bibRefs = {}
    if not args.overwrite:
        if os.path.exists(bibfile):
            bibRefs = ReadBibTeX(bibfile)
        else:
            args.overwrite = True

    # Read \cite IDs from .tex file and store in texRefs
    texRefs = RefsFromTeX(texfile)
    print('{} contains {} references.'.format(texfile, len(texRefs)))

    # Check for noinspire.bib file and read bibtex
    if os.path.exists('noinspire.bib'):
        noinspireRefs = ReadBibTeX('noinspire.bib')
    else:
        noinspireRefs = {}

    # New bibdata stored in writeRefs
    writeRefs = collections.OrderedDict()
    
    # Loop over references cited in .tex file
    skip = []
    texRepl = {}
    first = True
    for i, ref in enumerate(texRefs):

        # Skip duplicate references with different identifiers
        if i in skip:
            continue
        
        # Don't download data if it already exists in .bib file
        if (not args.overwrite) and ref in bibRefs:
            if args.inspire:
                if bibentry.inspireRE.match(ref) is not None:
                    continue
            elif args.arxiv:
                if bibentry.arxivRE.match(ref) is not None or bibentry.arxiv_oldRE.match(ref) is not None:
                    continue
            elif args.doi:
                if bibentry.doiRE.match(ref) is not None:
                    continue
            else:
                continue

        if first:
            print('Downloading data from Inspire...')
            first = False
        if args.verbose:
            print('\t{}'.format(ref))

        # Download bibtex from Inspire
        bibtex = GetInspireBibTeX(ref)

        # Select identifier to use
        if bibtex is not None:

            bib = bibentry.BibEntry(bibtex)
            ids = bib.IDs

            # Use inspire ID
            if args.inspire:
                tag = ids['inspire']

            # Use arXiv ID
            elif args.arxiv and ids['arxiv'] is not None:
                tag = ids['arxiv']

            # Use DOI
            elif args.doi and ids['doi'] is not None:
                tag = ids['doi']

            # Use existing identifier
            # If multiple are used preference is Inspire > arXiv > DOI
            else:
                if ids['inspire'] in texRefs:
                    tag = ids['inspire']

                elif ids['arxiv'] in texRefs:
                    tag = ids['arxiv']

                else:
                    tag = ids['doi']

            # Update dictionary of replacements for .tex file
            # to avoid duplicate bibliography entries
            if tag == ids['inspire']:
                if ids['arxiv'] in texRefs:
                    texRepl[ids['arxiv']] = ids['inspire']
                if ids['doi'] in texRefs:
                    texRepl[ids['doi']] = ids['inspire']

            elif tag == ids['arxiv']:
                if ids['inspire'] in texRefs:
                    texRepl[ids['inspire']] = ids['arxiv']
                if ids['doi'] in texRefs:
                    texRepl[ids['doi']] = ids['arxiv']

            elif tag == ids['doi']:
                if ids['arxiv'] in texRefs:
                    texRepl[ids['arxiv']] = ids['doi']
                if ids['inspire'] in texRefs:
                    texRepl[ids['inspire']] = ids['doi']

            # Add bibtex to output dictionary
            if not tag in bibRefs and not tag in writeRefs:
                bib.tag = tag
                writeRefs[tag] = bib

            # Skip duplicate references with different identifiers
            for id in ids.values():
                if id is not None and id != ref:
                    try:
                        skip.append(texRefs.index(id))
                    except:
                        ValueError

        # If reference can't be found on Inspire check noinspire.bib references
        else:
            try:
                writeRefs[ref] = noinspireRefs[ref]
            except KeyError:
                print("Could not find data for '{}'. Skipping.".format(ref))
            else:
                print("Reference '{}' not found on Inspire. Using noinspire.bib entry.".format(ref))
            continue

    # Write bib file
    if len(writeRefs) > 0:
        print('{} references added to .bib file.'.format(len(writeRefs)))
        if args.overwrite:
            mode = 'w'
        else:
            mode = 'a'

        with open(bibfile, mode) as f:
            for bib in writeRefs.values():
                f.write(bib.BibTeXString() + '\n')
    else:
        print('No new references to add.')

    # Update tex file to change identifiers or remove duplicates, if required
    if len(texRepl) > 0:
        if args.inspire or args.arxiv or args.doi:
            if args.inspire:
                ID_type = 'Inspire IDs'
            elif args.arxiv:
                ID_type = 'arXiv IDs'
            else:
                ID_type = 'DOIs'
            print("\nYou have selected to replace all identifiers with {}.".format(ID_type))
            ans = input('Are you sure you want to update the \cite commands in the tex file? (y/n): ')
        else:
            print('\nTeX file contains identical references with different identifiers.')
            ans = input('Do you want to update the \cite commands in the tex file? (order of preference is Inspire > arXiv > DOI) (y/n): ')
        
        while ans != 'y' and ans != 'n':
            ans = input("Please answer y or n: ")
        
        if ans == 'n':
            sys.exit()  

        UpdateTeXCite(texfile, texRepl)

##################################################

if __name__ == '__main__':
    main()

##################################################
