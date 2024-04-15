#!/usr/bin/python3

##################################################
"""bibentry.py: Class to store bibtex entries.

Copyright 2024 Peter Cox
"""

__author__ = "Peter Cox"
__email__ = "peter.cox@unimelb.edu.au"
__version__ = "1.0"

##################################################

import collections, re

##################################################

# Citation identifier types
arxivRE = re.compile(r'^\d{4}.\d{4,5}$')
arxiv_oldRE = re.compile(r'^[a-z.\-]+/[09]\d{6}$', re.IGNORECASE)
inspireRE = re.compile(r'^[a-zA-Z\-]+:\d{4}[a-z]{2,3}$')
doiRE = re.compile(r'^10.[0-9.]{4,}/\w+')

##################################################

class BibEntry:
    """Class to store bibtex entries."""

    ##############################

    def __init__(self, bibtex=None):
        """Initialise class instance and optionally store bibtex information."""
    
        self.IDs = {'arxiv': None, 'inspire': None, 'doi': None}
        self.tag = None
        self.info = collections.OrderedDict()

        if bibtex is not None:
            self.ReadBibTeX(bibtex)

    ##############################

    def __repr__(self):
        return 'bibentry.BibEntry({})'.format(self.BibTeXString())

    ##############################

    def __str__(self):
        return self.BibTeXString()

    ##############################

    def ReadBibTeX(self, bibtex):
        """Parse BibTeX string and store information."""

        sissa = False
        bibtex = bibtex.strip()

        if not bibtex.startswith('@'):
            raise ValueError("Invalid BibTeX string!")

        try:
            for line in bibtex.splitlines():

                # Get tag
                if line.startswith('@'):
                    self.tag = line.split('{')[1].split(',')[0]

                    # Check if it's a valid Inspire identifier
                    if inspireRE.match(self.tag) is not None:
                        self.IDs['inspire'] = self.tag

                # End of entry
                elif line.startswith('}'):
                    break

                # Parse data fields
                else:
                    s = line.split('=')
                    field = s[0].strip().lower()
                    data = s[1].strip()
                    if data.endswith(','):
                        data = data[:-1]

                    self.info[field] = data

                    # Get arXiv identifier
                    if field == 'eprint':
                        arxiv_id = data[1:-1]
                        if arxivRE.match(arxiv_id) is not None or arxiv_oldRE.match(arxiv_id) is not None:
                            self.IDs['arxiv'] = arxiv_id

                    # Get DOI
                    elif field == 'doi':
                        doi = data[1:-1]
                        if doiRE.match(doi) is not None:
                            self.IDs['doi'] = doi

                    # Check if SISSA journal (JCAP/JHEP)
                    elif field == 'journal' and (data == '"JCAP"' or data == '"JHEP"'):
                        sissa = True

            # Add 'number' field for JCAP and JHEP
            if sissa:
                self.info['number'] = self.info['year']

        except (IndexError, ValueError):
            raise ValueError("Invalid BibTeX string!")

    ##############################

    def BibTeXString(self):
        """Return BibTeX data as a string."""

        bibtex = '@article{{{},\n'.format(self.tag)

        for field, data in self.info.items():
            bibtex += '\t{} = {},\n'.format(field, data)

        bibtex = bibtex[:-2] + '\n}\n'

        return bibtex

##################################################