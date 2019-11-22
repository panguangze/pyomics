# coding: utf-8
# author: zachary

import os
import re
import warnings
import pymysql
import pysam

from pyomics.data.genotype import Genotype

# tool
bgzip = '/home/BIOINFO_TOOLS/mutation_tools/tabix/tabix-0.2.6/bgzip'
tabix = '/home/BIOINFO_TOOLS/mutation_tools/tabix/tabix-0.2.6/bgzip'
# reference
hg19_fasta = '/home/BIOINFO_DATABASE/reference/genome_DNA/Homo_sapiens/hg19/hg19.fa'
# ucsc_database
# get rs information from ucsc database
# https://genome.ucsc.edu/goldenpath/help/mysql.html
# table explanation
# http://genome.ucsc.edu/cgi-bin/hgTables
# mysql -h genome-mysql.cse.ucsc.edu -u genome -A -D hg19
ucsc_host = 'genome-mysql.cse.ucsc.edu'
ucsc_user = 'genome'
ucsc_database = 'hg19'
ucsc_table = 'snp138'
# dl380a database
# """MySql configuration"""
db_host = 'dl380a.cs.cityu.edu.hk'
db_user = 'root'
db_passwd = 'omics2017'
db_database = 'omics'

def getGenotypeHg19(chromosome, apos):
    if 'chr' not in chromosome:
        chromosome = 'chr' + chromosome.upper().strip()
    apos = int(apos)

    # open hg19.fa file
    if os.path.isfile(hg19_fasta):
        hg19 = pysam.FastaFile(hg19_fasta)      # Attention: Make sure the hg19_fasta is correct!
    else:
        raise Exception("Not Found Error: hg19.fa not found!")

    base = hg19.fetch(chromosome, apos, apos+1)
    base = str(base).upper()

    if base == '':
        raise Exception("Locus {0} is not found on chromosome {1}.".format(apos, chromosome))
    elif base in ['A', 'T', 'C', 'G']:
        genotype = Genotype([base, base])
    else:
        genotype = Genotype(['N', 'N'])

    genotype.isphased = True
    return genotype
