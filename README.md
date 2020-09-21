# BibGen
Script to automatically generate .bib files using the Inspire API.

## Usage
*bibgen.py \<TeXfile\> (--overwrite)*

## Details
Finds all \cite commands in a TeX file and downloads the corresponding BibTeX from the Inspire database.
Works with arXiv preprint number, Inspire TeXkey or DOI.

A check is also performed for \cite commands that point to the same reference using different identifiers. If necessary, the TeX file is updated to use a common identifier and avoid duplicate entries in the bibliography. The order of preference is: arXiv > Inspire > DOI.

The default behaviour is to append new references to an existing .bib file. This avoids unecessary calls to the Inspire API and can save significant time if there are a large number of references.
This behaviour can be changed using the --overwrite option. This is useful for obtaining updated citation information (e.g. preprints that have since been published).

References not available in the Inspire database can be included by placing the BibTeX in the file *noinspire.bib*. The advantage of this approach is that these references are not lost when using the --overwrite option. 
