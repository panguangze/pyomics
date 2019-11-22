# coding: utf-8
# author: zachary

# abbreviation codes for degenerate bases
DEGENERATE_BASES = {
    'A': ['A'],
    'T': ['T'],
    'C': ['C'],
    'G': ['G'],
    'M': ['A', 'C'],
    'R': ['A', 'G'],
    'W': ['A', 'T'],
    'S': ['C', 'G'],
    'Y': ['C', 'T'],
    'K': ['G', 'T'],
    'V': ['A', 'C', 'G'],
    'H': ['A', 'C', 'T'],
    'D': ['A', 'G', 'T'],
    'B': ['C', 'G', 'T'],
    'N': ['G', 'A', 'T', 'C']
}

class Genotype(object):
    __name__ = "Genotype"

    def __init__(self, alleles, samplename=None, isphased=False, isindel=False, issnp=False, issv=False):
        '''
        :param alleles: a pair of allele. E.g. ['A', 'T']
        :return:
        '''
        # convert alleles to upper case and sort it. Order: ['A', 'C', 'G', 'T', 'a', 'c', 'g', 't']
        # alleles.sort()  # sort alleles
        alleles = map(str.upper, alleles)

        self.alleles = alleles
        self.samplename = samplename
        self.isphased = isphased
        self.isindel = isindel  # insertion/deletion
        self.issnp = issnp      # single-nucleotide polymorphism
        self.issv = issv        # structure variation

    def __str__(self):
        return ''.join(self.alleles)

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, index):
        return self.alleles[index]

    def __setitem__(self, index, value):
        self.alleles[index] = value

    def addAllele(self, allele):
        self.alleles.append(allele)

    def variantType(self):
        if self.is_snp:
            return "snp"
        elif self.is_indel:
            return "indel"
        elif self.is_sv:
            return "sv"
        else:
            return "unknown"

    def countAllele(self, allele):
        return self.alleles.count(allele.strip().upper())

    def isEqual(self, genotype, strict=False):
        if isinstance(genotype, GenoType):
            nalleles = genotype.alleles
        else:
            nalleles = list(genotype.upper())

        # compare two genotypes
        result = 0  # 0: not matching, 1: exact matching, 2: fuzzy matching

        if len(nalleles) == len(self.alleles):
            if sorted(nalleles) == sorted(self.alleles):
                result = 1
            else:
                if self.fuzzycompare(nalleles):
                    result = 2
                else:
                    result = 0
        else:
            result = 0

        if result == 0:
            return False
        elif result == 1:
            return True
        elif result == 2:
            if strict:
                return False
            else:
                return True
        else:
            return False

    def fuzzycompare(self, nalles):
        from itertools import permutations

        for perm in permutations(self.alleles):
            is_match = True
            for index, allele in enumerate(perm):
                if allele not in DEGENERATE_BASES[nalles[index]]:
                    is_match = False
                    break  # break current for loop

            if is_match:
                return True
        return False

