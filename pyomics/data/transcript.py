# coding: utf-8
# author: zachary

import os
import re
import warnings
import pymysql

from pyomics.data.aux import *

class Transcript(object):
    __name__ = "Transcript"

    def __init__(self, transname, ensembleid=None):
        self.transname = transname
        self.ensembleid = ensembleid
        self.strand = None
        self.biotype = None
        self.chromosome = None
        self.exonCount = None
        self.exonLens = None
        self.cdsStarts = None
        self.cdsLens = None
        self.exonStarts = None

        # FIXME: search transcripts by transcript name and ensembleid
        conn = pymysql.connect(host=db_host, user=db_user, passwd=db_passwd, db=db_database)
        cur  = conn.cursor()

        try:
            # if ensemble id (public key) is provided
            if ensembleid:
                select_statement = "SELECT * FROM human_ens75_trans_psl WHERE trans_name='{}' and trans_ens_id='{}'".format(transname, ensembleid)
                cur.execute(select_statement)
            else:
                select_statement = "SELECT * FROM human_ens75_trans_psl WHERE trans_name='{}'".format(transname)
                cur.execute(select_statement)

            # No matching result.
            if cur.rowcount == 0:
                if ensembleid:
                    msg = "Transcript name [{0}] and ensemble id [{1}] not found.".format(transname, ensembleid)
                else:
                    msg = "Transcript name [{0}] not found.".format(transname)
                raise Exception(msg)
            # One match!
            elif cur.rowcount == 1:
                rowinfo = cur.fetchone()  # fetch one row from result

                # Init some basic info.
                self.ensembleid = rowinfo[1]
                self.strand = rowinfo[9]
                self.biotype = rowinfo[2]
                self.chromosome = rowinfo[3]
                self.exonCount = int(rowinfo[4])
                self.exonLens = [int(num) for num in filter(None, str(rowinfo[5]).split(','))]

                # coding start regions
                cdsregions = filter(None, rowinfo[6].split(','))  # CDS region info. E.g. 99840015(48),99840227(132),99848891(141),99849257(102),99852500(154),99854012(167),99854504(207),
                self.cdsStarts = []  # coding position start point
                self.cdsLens = []    # coding region length

                for cds in cdsregions:
                    startpos = int(cds.split('(')[0]) + 1  # transcript file has minus start pos by 1
                    cdslen = int(cds.split('(')[1].split(')')[0])
                    self.cdsStarts.append(startpos)
                    self.cdsLens.append(cdslen)

                self.exonStarts = [int(num)+1 for num in filter(None, str(rowinfo[7]).split(','))]  # transcript file has minus start pos by 1
            # More than one match!
            elif cur.rowcount >= 2:
                if ensembleid:
                    raise Exception("More than one records found for transcript name: [{0}] and ensemble id: [{1}]".format(transname, ensembleid))
                else:
                    availEnsembleid = []
                    for row in cur.fetchall():
                        availEnsembleid.append(row[1])
                    raise Exception("More than one records found for transcript name: [{0}]. Please specify the ensemble id. Available ensemble id: {1}.".format(transname, availEnsembleid))
        finally:
            cur.close()
            conn.close()


    def cdsscope(self):
        if self.biotype != 'protein_coding':
            return 0, 0

        start_pos = self.cdsStarts[0]
        end_pos = self.cdsStarts[-1] + self.cdsLens[-1] - 1

        return start_pos, end_pos

    def getAbsPosition(self, rpos):
        total_length = 0
        for val in self.exonLens:
            total_length += val

        if rpos > total_length or rpos < 1:
            raise Exception("Input relative position [{0}] is not in the range of transcript: {1} ~ {2}".format(rpos, 1, total_length))

        temp_pos = int(rpos)
        exon_idx = 0  # index of exon which rpos resides
        apos = 0

        if self.strand == '+':
            for idx, val in enumerate(self.exonLens):
                if temp_pos > int(val):
                    temp_pos -= int(val)
                else:
                    exon_idx = idx
                    break
            apos = int(self.exonStarts[exon_idx]) + temp_pos - 1  # minus 1 because relative pos starts from 1
        elif self.strand == '-':
            for idx, val in enumerate(reversed(self.exonLens)):
                if temp_pos > int(val):
                    temp_pos -= int(val)
                else:
                    exon_idx = len(self.exonLens) - idx - 1
                    break
            apos = self.exonStarts[exon_idx] + self.exonLens[exon_idx] - 1 - temp_pos + 1
        else:
            raise Exception("Invalid strand. Strand should be \'+\' or \'-\'")

        return apos

    def getAcidPosition(self, acidpos):
        base_arr = [(acidpos-1)*3+1, (acidpos-1)*3+2, (acidpos-1)*3+3]  # relative positions of codon bases on mRNA. Start from 1.
        abspos_arr = []

        if self.strand == '+':
            # calculate how many bases of exons are not in coding region.
            non_cd_len = 0  # length of non-coding region
            for idx, exon_s in enumerate(self.exonStarts):
                if int(exon_s) >= self.cdsStarts[0]:
                    break
                else:
                    if self.exonStarts[idx] + self.exonLens[idx] - 1 < self.cdsStarts[0]:
                        non_cd_len += self.exonLens[idx]
                    else:
                        non_cd_len += self.cdsStarts[0] - exon_s

            # get absolute position using function getAbsPosition
            try:
                for base in base_arr:
                    abspos_arr.append(self.getAbsPosition(base+non_cd_len))
            except Exception:
                raise Exception("Input acid position [{0}] is out of range".format(acidpos))
        elif self.strand == '-':
            # calculate how many bases of exons are not in coding region.
            non_cd_len = 0  # length of non-coding region
            cdsEnd = self.cdsStarts[-1] + self.cdsLens[-1] - 1
            for idx in reversed(range(0, len(self.exonStarts))):
                exon_e = self.exonStarts[idx] + self.exonLens[idx] - 1
                exon_s = self.exonStarts[idx]

                if int(exon_e) <= cdsEnd:
                    break
                else:
                    if int(exon_s) > cdsEnd:
                        non_cd_len += exon_e - exon_s + 1
                    else:
                        non_cd_len += exon_e - cdsEnd

            # get absolute position using function getAbsPosition
            try:
                for base in base_arr:
                    abspos_arr.append(self.getAbsPosition(base+non_cd_len))
            except Exception:
                raise Exception("Input acid position [{0}] is out of range".format(acidpos))
        else:
            raise Exception("Invalid strand. Strand should be \'+\' or \'-\'")

        return sorted(abspos_arr)

    def getRelPosition(self, apos):
        tsStart = self.exonStarts[0]  # start position of transcript
        tsEnd = self.exonStarts[-1] + self.exonLens[-1] - 1  # end position of transcript
        if apos < tsStart or apos > tsEnd:
            raise Exception("Input absolute position [{0}] is not in the range of transcript: {1} ~ {2}".format(apos, tsStart, tsEnd))

        temp_pos = int(apos)
        rpos = 0

        if self.strand == '+':
            for idx, start in enumerate(self.exonStarts):
                if temp_pos > start + self.exonLens[idx] - 1:
                    rpos += self.exonLens[idx]
                elif temp_pos >= start and temp_pos <= start + self.exonLens[idx] - 1:
                    rpos += temp_pos - start + 1
                    break
                else:
                    # absolute position is not in the range of exons
                    return -1
        elif self.strand == '-':
            total_exon_len = sum(self.exonLens)
            for idx, start in enumerate(self.exonStarts):
                if temp_pos > start + self.exonLens[idx] - 1:
                    rpos += self.exonLens[idx]
                elif temp_pos >= start and temp_pos <= start + self.exonLens[idx] - 1:
                    rpos += temp_pos - start + 1
                    break
                else:
                    # absolute position is not in the range of exons
                    return -1
            rpos = total_exon_len - rpos + 1

        else:
            raise Exception("Invalid strand. Strand should be \'+\' or \'-\'")

        return rpos

    def getCodon(self, acidpos):
        abspos_arr = self.getAcidPosition(acidpos)
        return abspos_arr
        # return str(getCodonHg19(self.chromosome, self.strand, abspos_arr)).upper()
