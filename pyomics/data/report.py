# coding: utf-8
# author: zachary

import os
import shutil
import uuid
from jinja2 import Environment, FileSystemLoader
import codecs

basedir = os.path.dirname(os.path.abspath(__file__))

def render(htmlpath, context={}):
    # Capture directory name of the html.
    dirname = os.path.dirname(htmlpath)
    basename = os.path.basename(htmlpath)

    # Create the jinja2 environment.
    # Notice the use of trim_blocks, which greatly helps control whitespace.
    j2_env = Environment(loader=FileSystemLoader(dirname), trim_blocks=True)
    template = j2_env.get_template(basename)

    resulthtml = template.render(context)

    with codecs.open(htmlpath, 'w', encoding='utf-8') as f:
        f.write(resulthtml)

def writeReport(input, output, context={}):
    input = str(input)
    outpath  = os.path.dirname(output)

    # check static folder in output directory
    if not os.path.isdir(os.path.join(outpath, "static")):
        try:
            os.mkdir(os.path.join(outpath, "static"))
        except:
            raise

    # generate json for generate report
    report_json = {}
    if os.path.exists(input):
        filename = os.path.basename(input)
        filext   = os.path.splitext(input)[1].lower()

        hashname = os.path.join("static", str(uuid.uuid1()))
        copypath = os.path.join(outpath, hashname)

        shutil.copyfile(input, copypath)

        # Images
        if filext in [".tif", ".tiff", ".gif", ".jpeg", ".jpg", ".png"]:
            report_json = {
                "type": "image",
                "value": filename,  # use file name here, because we need relative path in html report
                "filename": hashname
            }
        # pdf
        elif filext in [".pdf"]:
            report_json = {
                "type": "pdf",
                "value": filename,
                "filename": hashname
            }
        # html
        elif filext in [".html", ".htm"]:
            # render html
            # replace the files in context to media path
            for key in context:
                # if value is a file path
                if type(context[key]) is str and os.path.exists(context[key]):
                    # copy to static folder and update context
                    newname = str(uuid.uuid1())
                    newpath = os.path.join(outpath, "static", newname)
                    shutil.copyfile(context[key], newpath)
                    context[key] = newname  # do not need static here, because html and context file are in the same static folder. Only need file name for relative path

            render(copypath, context)

            report_json = {
                "type": "html",
                "value": filename,
                "filename": hashname
            }
        # the remaining are treated as text
        else:
            report_json = {
                "type": "text",
                "value": filename,
                "filename": hashname
            }

    # input is just a string
    else:
        report_json = {
            "type": "string",
            "value": input,
            "filename": ""
        }

    # generate report
    j2_env = Environment(loader=FileSystemLoader(basedir), trim_blocks=True)
    template = j2_env.get_template('omics-report.html')

    content = ""
    if report_json["type"] == "string":
        content += "<p>{0}</p>".format(report_json["value"])
    elif report_json["type"] == 'image':
        content += "<img src=\"{0}\" />".format(report_json["filename"])
    elif report_json["type"] == 'pdf':
        content += "<object data=\"{0}\" type=\"application/pdf\" ></object>".format(report_json["filename"])
    elif report_json["type"] == 'html':
        content += "<iframe src=\"{0}\" scrolling=\"no\" frameborder=\"0\"></iframe>".format(report_json["filename"])
    elif report_json["type"] == 'text':
        content += "<a href=\"{0}\">{1}</a>".format(report_json["filename"], report_json["value"])
        with open(os.path.join(outputpath, report_json["filename"]), 'r') as f:
            text_content = ''.join(f.readlines())
        content += "<pre>{0}</pre>".format(text_content)

    resulthtml = template.render(content=content.decode('utf-8'))

    with codecs.open(output, 'w', encoding='utf-8') as f:
        f.write(resulthtml)
