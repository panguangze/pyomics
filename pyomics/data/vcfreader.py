# coding: utf-8
# author: zachary

import vcf
import os
import warnings
import re
import pymysql

from pyomics.data.aux import *
from pyomics.data.codon import Codon
from pyomics.data.transcript import Transcript
from pyomics.data.refgene import RefGene
from pyomics.data.genotype import Genotype


class VCFReader(vcf.parser.Reader):
    __name__ = "VCFReader"

    def __init__(self, filename):
        if not str(filename).lower().endswith('.gz'): # compress first
            os.system('{0} -c {1} > {1}.gz'.format(bgzip, filename))
            filename = filename + '.gz'
        if not os.path.exists("{0}.tbi".format(filename)): # make index
            # build index
            os.system('{} -p vcf {}'.format(tabix, filename))
        super(VCFReader, self).__init__(filename=filename)

    def genotype(self, chromosome, apos, reference=True):
        chrom = str(chromosome).lower()
        chrom = chrom.replace('chr', '') if 'chr' in chrom else chrom
        apos = int(apos)
        record = None

        try:
            queryset = self.fetch(chrom, apos-1, apos)
            for result in queryset:
                record = result
        except ValueError as e:
            pass
            # warnings.warn("Chromosome {} not found in vcf.".format(chrom), UserWarning)

        # no record found
        if not record:
            if reference:
                genotype = getGenotypeHg19(chromosome, apos)
            else:
                raise ValueError("Chromosome {}, Position {} not found in vcf file and hg19 reference".format(
                    chromosome, apos))
        else:
            genotype = self.buildGenotype(record, 0)

        return genotype

    def genotypeRS(self, rsname, reference=True):
        conn = pymysql.connect(host=ucsc_host, user=ucsc_user, db=ucsc_database)
        cur  = conn.cursor()

        try:
            select_statement = "SELECT * FROM {} WHERE name='{}'".format(ucsc_table, rsname)
            cur.execute(select_statement)

            if cur.rowcount == 1:
                rowinfo = cur.fetchone()
                return self.genotype(rowinfo[1], rowinfo[2], reference)
            elif cur.rowcount == 0:
                raise KeyError("Cannot find item by rsname {} in ucsc database".format(rsname))
            else:
                raise KeyError("Multiple items found by rsname {} in ucsc database".format(rsname))
        finally:
            cur.close()
            conn.close()

    def buildGenotype(self, record, sampleidx=0):
        gt = record.samples[sampleidx]['GT']

        # All samples must have GT call information; if a call cannot be made for a sample at a given locus,
        # ”.” must be specified for each missing allele in the GT field (for example ./. for a diploid).
        # The meanings of the separators are:
        # / : genotype unphased
        # | : genotype phased
        alleles = []
        gt_arr = re.split('/|\|', gt)

        for allele in gt_arr:
            if allele == '0':
                alleles.append(record.REF)  # reference locus
            elif allele == 'N':
                alleles.append(allele)  # call cannot be made, 'N': ['G', 'A', 'T', 'C']
            else:
                call_index = int(allele) - 1
                if call_index >= len(record.ALT) or record.ALT[call_index] is None:
                    alleles.append('')  # deletion, empty
                else:
                    alleles.append(str(record.ALT[call_index]))


        genotype = Genotype(alleles)
        genotype.issnp = record.is_snp
        genotype.isindel = record.is_indel
        genotype.issv = record.is_sv
        genotype.isphased = record.samples[sampleidx].phased
        genotype.samplename = record.samples[sampleidx].sample

        return genotype

    def genotypeByTranscript(self, transname, rpos, ensembleid=None, reference=True):
        transcript = Transcript(transname, ensembleid)
        apos = transcript.getAbsPosition(rpos)
        return self.genotype(transcript.chromosome, apos, reference)

    def codonByTranscript(self, transname, acidpos, ensembleid=None, reference=True):
        transcript = Transcript(transname, ensembleid)
        apos_arr = transcript.getAcidPosition(acidpos)
        genotype_arr = [self.genotype(transcript.chromosome, apos, reference) for apos in apos_arr]
        return self.codonCombinations(genotype_arr, transcript.strand)

    def codonCombinations(self, genotypes, strand):
        assert len(genotypes) == 3
        codons = []  # codon combinations

        basestr = (genotypes[0][0] + genotypes[1][0] + genotypes[2][0])[:3]
        codons.append(basestr)
        basestr = (genotypes[0][1] + genotypes[1][1] + genotypes[2][1])[:3]
        codons.append(basestr)

        # all phased
        if genotypes[0].isphased and genotypes[1].isphased and genotypes[2].isphased:
            pass
        # genotype 0 is unphased
        if not genotypes[0].isphased:
            basestr = (genotypes[0][1] + genotypes[1][0] + genotypes[2][0])[:3]
            codons.append(basestr)
            basestr = (genotypes[0][0] + genotypes[1][1] + genotypes[2][1])[:3]
            codons.append(basestr)
        # genotype 1 is unphased
        if not genotypes[1].isphased:
            basestr = (genotypes[0][0] + genotypes[1][1] + genotypes[2][0])[:3]
            codons.append(basestr)
            basestr = (genotypes[0][1] + genotypes[1][0] + genotypes[2][1])[:3]
            codons.append(basestr)
        # genotype 2 is unphased
        if not genotypes[2].isphased:
            basestr = (genotypes[0][0] + genotypes[1][0] + genotypes[2][1])[:3]
            codons.append(basestr)
            basestr = (genotypes[0][1] + genotypes[1][1] + genotypes[2][0])[:3]
            codons.append(basestr)

        # remove duplicates
        codons = list(set(codons))
        codonobjs = []
        for codon in codons:
            codonobjs.append(Codon(codon, strand))
        return codonobjs

    def genotypeByRefGene(self, transname, rpos, reference=True):
        ref = RefGene(transname)
        apos = ref.getAbsPosition(rpos)
        return self.genotype(ref.chromosome, apos, reference)

    def codonByRefGene(self, transname, acidpos, reference=True):
        ref = RefGene(transname)
        apos_arr = ref.getAcidPosition(acidpos)

        genotype_arr = [self.genotype(ref.chromosome, apos, reference) for apos in apos_arr]
        return self.codonCombinations(genotype_arr, ref.strand)

    def findNonsenses(self, transname, ensembleid=None, reference=True):
        transcript = Transcript(transname, ensembleid)
        cdsS, cdsE = transcript.cdsscope()
        # read vcf file
        try:
            records = self.fetch(transcript.chromosome, cdsS-1, cdsE)
        except ValueError:
            records = []

        nonsenses = []

        for record in records:
            # a nonsense mutation is a point mutation in a sequence of DNA that results in a premature stop codon, or a nonsense codon in the transcribed mRNA
            if record.is_snp:
                relpos = transcript.getRelPosition(record.POS)  # relative position of base on mRNA. Start from 1.
                acidpos = relpos//3 + 1  # amino acid position
                codons = self.codonByTranscript(transname, acidpos, ensembleid, reference)

                # count the stop codons in all codon cobinations
                cnt = 0
                for codon in codons:
                    if str(codon) in ['UAA', 'UAG', 'UGA']:  # stop codon
                        cnt += 1

                # all possible codons are stop codon
                if cnt > 0:
                    nonsenses.append([record.POS, acidpos, cnt, len(codons)])

        return nonsenses

    def findFrameshifts(self, transname, ensembleid=None, reference=True):
        transcript = Transcript(transname, ensembleid)
        cdsS, cdsE = transcript.cdsscope()
        # read vcf file
        try:
            records = self.fetch(transcript.chromosome, cdsS-1, cdsE)
        except ValueError:
            records = []

        frameshifts = []

        for record in records:
            # A frameshift mutation (also called a framing error or a reading frame shift) is a genetic mutation caused by indels (insertions or deletions) of a number of nucleotides in a DNA sequence that is not divisible by three
            if record.is_indel:
                gt = self.genotype(transcript.chromosome, record.POS, reference)
                for allele in gt.alleles:
                    if (len(allele)-1) % 3 != 0:
                        relpos = transcript.getRelPosition(record.POS)  # relative position of base on mRNA. Start from 1.
                        frameshifts.append([record.POS, relpos])
        return frameshifts
