# coding: utf-8
# author: zachary

import os
import re
import warnings

from pyomics.data.aux import *

class RefGene(object):
    __name__ = "RefGene"

    def __init__(self, transname):
        self.transname = transname
        self.chromosome = None
        self.strand = None
        self.cdsStart = None
        self.cdsEnd = None
        self.exonStarts = None
        self.exonEnds = None

        conn = pymysql.connect(host=db_host, user=db_user, passwd=db_passwd, db=db_database)
        cur = conn.cursor()
        select_statement = "SELECT * FROM refGene where name='{}'".format(transname)
        cur.execute(select_statement)

        if cur.rowcount == 0:
            rowinfo = None
        elif cur.rowcount == 1:
            rowinfo = cur.fetchone()  # fetch one row from result
        elif cur.rowcount >= 2:
            rowinfo = None

        if rowinfo:
            self.chromosome = rowinfo[2]
            self.strand = rowinfo[3]
            self.cdsStart = int(rowinfo[6])
            self.cdsEnd = int(rowinfo[7])
            self.exonStarts = [int(num) for num in filter(None, str(rowinfo[9]).split(','))]   # split and remove empty elements in list
            self.exonEnds = [int(num) for num in filter(None, str(rowinfo[10]).split(','))]

        cur.close()
        conn.close()

    def getAbsPosition(self, rpos):
        exon_len_list = []  # store exons length in list
        total_length = 0

        for idx, val in enumerate(self.exonStarts):
            exon_len = int(self.exonEnds[idx]) - int(val) + 1
            exon_len_list.append(exon_len)
            total_length += exon_len

        if rpos > total_length or rpos < 1:
            raise Exception("Input relative position [{0}] is not in the range of transcript: {1} ~ {2}".format(rpos, 1, total_length))

        temp_pos = int(rpos)
        exon_idx = 0  # index of exon which rpos resides
        apos = 0

        if self.strand == '+':
            for idx, val in enumerate(exon_len_list):
                if temp_pos > int(val):
                    temp_pos -= int(val)
                else:
                    exon_idx = idx
                    break
            apos = int(self.exonStarts[exon_idx]) + temp_pos - 1  # minus 1 because relative pos starts from 1
        elif self.strand == '-':
            for idx, val in enumerate(reversed(exon_len_list)):
                if temp_pos > int(val):
                    temp_pos -= int(val)
                else:
                    exon_idx = len(exon_len_list) - idx - 1
                    break
            apos = int(self.exonEnds[exon_idx]) - temp_pos + 1
        else:
            raise Exception("Invalid strand. Strand should be \'+\' or \'-\'")

        return apos

    def getAcidPosition(self, acidpos):
        base_arr = [(acidpos-1)*3+1, (acidpos-1)*3+2, (acidpos-1)*3+3]  # relative positions of codon bases on mRNA. Start from 1.
        apos_arr = []

        if self.strand == '+':
            # calculate how many bases of exons are not in coding region.
            non_cd_len = 0  # length of non-coding region
            for idx, exon_s in enumerate(self.exonStarts):
                if int(exon_s) >= self.cdsStart:
                    break
                else:
                    if int(self.exonEnds[idx]) < self.cdsStart:
                        non_cd_len += int(self.exonEnds[idx]) - exon_s + 1  # 1 means plussing the exonEnd base
                    else:
                        non_cd_len += self.cdsStart - exon_s

            # get absolute position using function getAbsPosition
            try:
                for base in base_arr:
                    apos_arr.append(self.getAbsPosition(base+non_cd_len))
            except Exception:
                raise Exception("Input acid position [{0}] is out of range".format(acidpos))
        elif self.strand == '-':
            # calculate how many bases of exons are not in coding region.
            non_cd_len = 0  # length of non-coding region
            for idx in reversed(range(0, len(self.exonEnds))):
                exon_e = self.exonEnds[idx]
                exon_s = self.exonStarts[idx]

                if int(exon_e) <= self.cdsEnd:
                    break
                else:
                    if int(exon_s) > self.cdsEnd:
                        non_cd_len += exon_e - exon_s + 1
                    else:
                        non_cd_len += exon_e - self.cdsEnd

            # get absolute position using function getAbsPosition
            try:
                for base in base_arr:
                    apos_arr.append(self.getAbsPosition(base+non_cd_len))
            except Exception:
                raise Exception("Input acid position [{0}] is out of range".format(acidpos))
        else:
            raise Exception("Invalid strand. Strand should be \'+\' or \'-\'")

        return sorted(apos_arr)
