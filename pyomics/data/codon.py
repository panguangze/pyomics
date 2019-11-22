# coding: utf-8
# author: zachary

import os
import warnings
import re

class Codon(object):
    __name__ = 'Codon'

    def __init__(self, dnacodon, strand='-', isphased=False):
        dnacodon = dnacodon.strip().upper()
        if len(dnacodon) != 3:
            raise ValueError("Codon Error, DNA codon length is not 3")
        if not re.match("^[ATCG]*$", dnacodon):
            raise ValueError("Codon Error, DNA codon should only contain ATCG")
        self.isphased = isphased

        pair = {
                "A": "U",
                "T": "A",
                "C": "G",
                "G": "C"
                }
        bases = ""
        if strand == "+":
            bases = dnacodon.replace("T", "U")
        elif strand == "-":
            bases = ''.join([pair[base] for base in dnacodon])
        else:
            raise ValueError("Strand Error, Invalid strand value")
        self.bases = bases

    def __str__(self):
        return self.bases

    def __repr__(self):
        return self.__str__()
