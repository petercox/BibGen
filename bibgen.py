#!/usr/bin/python3

"""bibgen.py: Script to automatically generate .bib files.

usage: bibgen.py <texfile> (--append)

Parses a tex file for \cite commands and dowloads citation information from Inspire using the API.
Works with arXiv identifier, Inspire TeXkey or DOI.

The --append option appends new references to an existing bib file. 

References not available on Inspire can be included in the output bib file by placing them in the file noinspire.bib.
"""

__author__ = "Peter Cox"
__version__ = "2.1"
__date__  = "20-09-2020"


import os.path, re, sys, urllib.request


def RefsFromBib(bibfile):
	"""Read references from bib file."""

	bibRefs = []
	with open(bibfile) as f:
		for line in f:
			if line.startswith('@'):
				bibRefs.append(line.split('{',1)[1].rsplit(',')[0])

	return bibRefs


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

	uniqueRefs = RemoveDuplicateRefs(texRefs)
	return uniqueRefs


def RemoveDuplicateRefs(refs):
	"""Remove duplicate references from a list."""

	uniqueRefs = []
	for ref in refs:
		if ref.startswith('*'):
			ref = ref[1:]
		if ref not in uniqueRefs:
			uniqueRefs.append(ref)

	return uniqueRefs


def GetInspireBibtex(ref):
	"""Get bibtex information using Inspire API.
	
	Works with arXiv identifier, Inspire TeXkey, or DOI.
	"""

	# Determine citation type
	arxiv = re.compile(r'^\d{4}.\d{4,5}$')
	arxiv_old = re.compile(r'^[a-z.\-]+/[09]\d{6}$', re.IGNORECASE)
	inspire = re.compile(r'^[a-zA-Z\-]+:\d{4}[a-z]{2,3}$')
	doi = re.compile(r'^10.[0-9.]{4,}/\w+')

	if arxiv.match(ref) is not None or arxiv_old.match(ref) is not None:
		identifier = 'arxiv'
	elif inspire.match(ref) is not None:
		identifier = 'texkey'
	elif doi.match(ref) is not None:
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


if __name__ == '__main__':

	# Parse command line
	if len(sys.argv) < 2:
		print('usage: bibgen.py <texfile> (--append)')
		sys.exit(-1)

	texfile = sys.argv[1]
	append = False
	try:
		if sys.argv[2] == '-a' or sys.argv[2] == '--append':
			append = True
	except IndexError:
		pass

	base = texfile.rsplit('tex', 1)
	if len(base) == 1:
		print('Error: {} is not a valid .tex file.'.format(texfile))
		sys.exit(1)
	bibfile = base[0] + 'bib' 

	if append == False and os.path.exists(bibfile):
		ans = input('Warning this will overwrite existing bib file. Do you want to continue? (y/n): ')
		while ans != 'y' and ans != 'n':
			ans = input("Please answer y or n: ")
        
		if ans == 'n':
			sys.exit()

    # Read citations from existing bib file if updating
	if append == True:
		bibRefs = RefsFromBib(bibfile)

    # Read citations from tex file
	texRefs = RefsFromTex(texfile)
	print('Found %d references.'%len(texRefs))

	# Check for non-inspire bib file
	noinspire = {}
	ref = None
	if os.path.exists('noinspire.bib'):
		with open('noinspire.bib') as f:
			for line in f:
				if line.startswith('@'):
					if ref is not None:
						noinspire[ref] = data
					ref = line.split('{',1)[1].rsplit(',',1)[0]
					data = ''
				if ref is not None:
					data += line
			if ref is not None:
				noinspire[ref] = data

	# Download citation data from inspire and write bib file
	if append == True:
		mode = 'a'
	else:
		mode = 'w'

	with open(bibfile, mode) as f:
		for ref in texRefs:

			# Skip existing refs in bib file if updating
			if append == True:
				try:
					bibRefs.index(ref)
					continue
				except ValueError:
					pass

			# Get bibtex from inspire
			bibtex = GetInspireBibtex(ref)

			if bibtex is not None:
				bibdata = bibtex.split('{', 1)
				ref_type = bibdata[0]
				ref_details = bibdata[1].split(',',1)[1]
				ref_details = ref_details.replace('&gt','>').replace('&lt','<')            
				f.write('%s{%s,%s\n'%(ref_type,ref,ref_details))

			# No inspire reference
			else:
				try:
					f.write(noinspire[ref])
				except KeyError:
					print('Could not find reference for {}. Skipping.'.format(ref))
				else:
					print('Could not find inspire reference for {}. Using noinspire.bib entry.'.format(ref))
				continue