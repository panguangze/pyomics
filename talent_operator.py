# from infres.utils.talent_utils import get_var_gt
import json
import pandas as pd
import difflib
import warnings
from Bio import SeqIO
import sys
from functools  import reduce
HG19_PATH = "/home/troyee/bries/exps/assets/defaultFiles/hg19.fa"
TALENT_INPUT_TEMPLATE_PATH = "/home/troyee/bries/exps/talent_input_template.json"
TALENT_CONTENT_TEMPLATE_PATH = "/home/troyee/bries/exps/report_content_tmp.json"
TALENT_SCORE_TABLE = "/home/troyee/bries/exps/assets/defaultFiles/天赋基因打分表.xlsx"


def load_reference_to_dict(inf, format="fasta"):
    return {seq_record.id: seq_record.seq for seq_record in SeqIO.parse(inf, format)}
# hg19 = pyfastx.Fasta(hg19_path)


hg19 = load_reference_to_dict(HG19_PATH)
score_table = pd.read_excel(TALENT_SCORE_TABLE).fillna(method="ffill")


def string_similar_ratio(string1, string2):
    return difflib.SequenceMatcher(lambda x: x == " ", string1, string2).ratio()


def is_gt_equal(gt1, gt2):
    gt1 = gt1.upper()
    gt2 = gt2.upper()
    return gt1 == gt2 or gt1[::-1] == gt2


def get_score(project, gene, dbsnp, gt, sim_ratio=.6):
    # check project title
    _ = score_table[score_table.apply(lambda x: string_similar_ratio(x.Project, project) > sim_ratio, axis=1)]
    if len(_) == 0:
        warnings.warn("Cannot find project {} in score table".format(project), RuntimeWarning)
    # check gene and dbsnp
    _ = _[(_.Gene == gene) & (_.dbSNP == dbsnp)]
    if len(_) == 0:
        warnings.warn("Cannot find with gene {}, dbsnp {} in score table{}".format(gene, dbsnp, gt),
                      RuntimeWarning)
    # check genotype
    _ = _[_.apply(lambda x: is_gt_equal(x.GT, gt), axis=1)]
    # if len(_) > 1:
    #     warnings.warn("Multiple records find with gene {}, dbsnp {}, gt {} in score table, return the first one".format(
    #         gene, dbsnp, gt), RuntimeWarning)
    # elif len(_) == 0:
    #     warnings.warn("Cannot find with genotype {}".format(gt), RuntimeWarning)
    #     return 0
    return int(_.score.values[0])


def get_hg19_reference(chrom, start, stop=None):
    stop = start if stop is None else stop - 1
    start = start - 1    # string index start with 0
    return str(hg19[chrom][start:stop]).upper()


def get_non_mut_gt(chrom, pos):
    return get_hg19_reference(chrom, pos) * 2


def get_res(item, gene, id):
    for v in resultList:
        if v.belongs_to_item == item and \
            v.belongs_to_gene == gene and \
                v.id == id:
            return v
    return None


def get_cate_total_score(have_list):
    score = 0
    max_score = 0
    for item in itemList:
        if item.sub_sub_name in have_list:
            score = score + item.score
            max_score = max_score + item.max_score
    return score, max_score


def get_cate_total_max_score():
    pass


def get_cate(name):
    for cate in categoryList:
        if cate.name == name:
            return cate
    return None


def get_var_gt(x, y, gt):
    var = _pd_vars[(_pd_vars.Chr == x) & (_pd_vars.Start == y)]
    if var:
        ref = var.Ref
        alt = var.Alt
        Heterozygous = var.Heterozygous
        gt_list = list(gt)
        if Heterozygous == "1":
            gt_list[1] == alt
            genotype = ''.join(gt_list)
        if Heterozygous == "0":
            genotype = alt*2
    else:
        return None


def get_conclusion(item_name):
    score = 0
    max_score = 0
    score = [item.score for item in itemList if item.sub_sub_name == item_name][0]
    max_score = [item.max_score for item in itemList if item.sub_sub_name == item_name][0]
    if 0 <= score/max_score < 0.6:
        return "综合" + item_name + "水平欠佳"
    elif 0.6 <= score/max_score < 0.8:
        return "综合" + item_name + "与一般人相似"
    elif 0.8 <= score/max_score <= 1:
        return "综合" + item_name + "水平高于一般人"
    else:
        return "404"


class Result:
    def __init__(self, res):
        self.__dict__ = res
        self.gene = ""
        self.belongs_to_gene = ""
        self.belongs_to_item = ""


class Gene:
    def __init__(self, gene):
        self.__dict__ = gene


class Item:
    def __init__(self, item):
        self.__dict__ = item


class Group:
    def __init__(self, group):
        self.__dict__ = group


class Category:
    def __init__(self):
        self.name = ""
        self.have = []
        self.total_score = 0
        self.total_max_score = 0


# initialize object
resultList = []
geneList = []
itemList = []
groupList = []
categoryList = []
with open(TALENT_INPUT_TEMPLATE_PATH, encoding="utf-8") as f:
    product = json.load(f)

for sub_chapter in product["chapter_2"]["sub_chapter"]:
    groupList.append(Group(sub_chapter))
    for sub_content in sub_chapter["sub_content"]:
        itemList.append(Item(sub_content))
        for sub_sub_content in sub_content["sub_sub_content"]:
            geneList.append(Gene(sub_sub_content))
            for res in sub_sub_content["result"]:
                r = Result(res)
                r.belongs_to_gene = sub_sub_content["gene"]
                r.belongs_to_item = sub_content["sub_sub_name"]
                resultList.append(r)

for var in resultList:
    # print(var.id, var.position, var.genetype, var.belongs_to_item)
    gt = get_non_mut_gt(var.chromsome, int(var.position))
    gt_var = get_var_gt(var.chromsome, int(var.position), gt)
    if gt_var is not None:
        gt = gt_var
    dbSNP = var.id.replace("HGC0", "rs")
    score = get_score(var.belongs_to_item, var.belongs_to_gene, dbSNP, gt)
    # score = 1
    var.score = score
    var.max_score = 3
    # print(score)


# generate input data structure
for item in itemList:
    score = 0
    max_score = 0
    for gene in item.sub_sub_content:
        for res in gene["result"]:
            r = get_res(item.sub_sub_name, gene["gene"], res["id"])
            score = score + r.score
            max_score = max_score + r.max_score
    item.score = score
    item.max_score = max_score


for sub_chapter in product["chapter_1"]["sub_chapter"]:
    c = Category()
    c.name = sub_chapter["name"]
    have_list = []
    for have in sub_chapter["table"]:
        have_list.append(have["item"])
    c.have = have_list
    c.total_score, c.total_max_score = get_cate_total_score(have_list)
    categoryList.append(c)


cate_score_dict = {}
for table in product["chapter_1"]["analysis"]["table"]["table_content"]:
    cate_score = get_cate(table["cn_name"]).total_score
    table["score"] = cate_score
    cate_score_dict[table["cn_name"]] = cate_score
score_list = list(cate_score_dict.values())
product["chapter_1"]["analysis"]["table"]["score"] = score_list
# product["chapter_1"]["analysis"]["total_score"] = reduce(lambda x, y: x+y, score)
product["chapter_1"]["analysis"]["total_score"] = sum(score_list)


for sub_chapter in product["chapter_1"]["sub_chapter"]:
    for table in sub_chapter["table"]:
        table["result"] = get_conclusion(table["item"])
        print(table["item"])
        print(table["result"])

# check
with open("o.json", "w") as f:
    json.dump(product, f, ensure_ascii=False)

with open(TALENT_CONTENT_TEMPLATE_PATH) as c:
    content = json.load(c)

data = {
    "content": content,
    "product": product
    }

register(data, "talent_input")
