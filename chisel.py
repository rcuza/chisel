#!/usr/bin/env python
# encoding: utf-8

# Chisel
# David Zhou, github.com/dz
#
# Updates and enhancements added/included by ckunte:
# 14.05.2012:
# - RSS feed generator script, hat-tip: Ronan Jouchet, github.com/ronjouch
# - Smartypants content parsing included by ckunte, github.com/ckunte
# - Permalink url updated to include only the year followed by post title, 
#   i.e., http://staticsite.com/2012/post.html or http://staticsite.com/2012/post
#
# Requires:
# jinja2, markdown, mdx_smartypants, PyRSS2Gen

import sys, re, time, os, codecs
import jinja2, markdown, mdx_smartypants, PyRSS2Gen
import datetime
import ConfigParser
from email.parser import Parser

#Settings
# There is a lot of flexibility in how you can setup your files.
# A common setup is to keep native post files and the generated html 
# separate:
# WorkingDir
#     /chisel.py          (the generator)
#     /posts/             (markdown post files)
#     /blog.example.com/  (the generated html site from post files)
#     /templates/         (template files)

config_file = ("./example.com.ini")
config = ConfigParser.ConfigParser()
config.read(config_file)

BASEURL = config.get("GENERAL", "baseurl")
# The following tells chisel where to look for native posts:
source_path = config.get("GENERAL", "source_path")
#  The following tells chisel where to generate site:
DESTINATION = config.get("GENERAL", "destination_path")
HOME_SHOW = 3 #numer of entries to show on homepage
TEMPLATE_PATH = config.get("GENERAL", "templates_path")
TEMPLATE_OPTIONS = {}
TEMPLATES = dict(config.items("TEMPLATES"))
TIME_FORMAT = config.get("GENERAL", "time_format")
ENTRY_TIME_FORMAT = config.get("GENERAL", "entry_time_format")
#FORMAT should be a callable that takes in text
#and returns formatted text
FORMAT = lambda text: markdown.markdown(text, ['footnotes','smartypants',])
# default URLEXT = ".html"
# set URLEXT = "" if server recognizes .html URLs and can be linked-to without the extension part.
URLEXT = ".html"
# default PATHEXT = ""
# set PATHEXT = "" if URLEXT = ".html" and vice versa.
PATHEXT = ""
RSS = PyRSS2Gen.RSS2(
    title = "ckunte.net log",
    link = BASEURL + "rss.xml",
    description = "ckunte.net log",
    lastBuildDate = datetime.datetime.now(),
    items = [])
#########

STEPS = []

def step(func):
    def wrapper(*args, **kwargs):
        print "Starting " + func.__name__ + "...",
        func(*args, **kwargs)
        print "Done."
    STEPS.append(wrapper)
    return wrapper

def get_tree(source):
    files = []
    for root, ds, fs in os.walk(source):
        for name in fs:
            if name[0] == ".": continue
            path = os.path.join(root, name)
            f = open(path, "rU")
            ff = Parser().parse(f)
            title = ff['Subject']
            date = time.strptime(ff['Date'], ENTRY_TIME_FORMAT)
            year, month, day = date[:3]
            files.append({
                'title': title,
                'epoch': time.mktime(date),
                'content': FORMAT(''.join(ff._payload.decode('UTF-8'))),
                #'url': '/'.join([str(year), "%.2d" % month, "%.2d" % day, os.path.splitext(name)[0] + ".html"]),
                # Uncheck the following line if you have no rewrite (URLs end with .html).
                'url': '/'.join([str(year), os.path.splitext(name)[0] + URLEXT]),
                'pretty_date': time.strftime(TIME_FORMAT, date),
                'date': date,
                'year': year,
                'month': month,
                'day': day,
                'filename': name,
            })
            f.close()
    return files

def compare_entries(x, y):
    result = cmp(-x['epoch'], -y['epoch'])
    if result == 0:
        return -cmp(x['filename'], y['filename'])
    return result

def write_file(url, data):
    path = DESTINATION + url + PATHEXT
    dirs = os.path.dirname(path)
    if not os.path.isdir(dirs):
        os.makedirs(dirs)
    file = open(path, "w")
    file.write(data.encode('UTF-8'))
    file.close()

@step
def generate_homepage(f, e):
    """Generate homepage"""
    template = e.get_template(TEMPLATES['home'])
    write_file("index" + URLEXT, template.render(entries=f[:HOME_SHOW]))

@step
def generate_rss(f, e):
    """Generate rss"""
    for file in f[:HOME_SHOW]:
        RSS.items.append(PyRSS2Gen.RSSItem(title=file['title'], link=BASEURL + file['url'], description=file['content'], author="Chyetanya Kunte", guid = PyRSS2Gen.Guid(BASEURL + file['url']), pubDate=datetime.datetime(file['year'], file['month'], file['day'])))
    RSS.write_xml(open(DESTINATION + "rss.xml", "w"))

@step
def master_archive(f, e):
    """Generate master archive list of all entries"""
    template = e.get_template(TEMPLATES['archive'])
    write_file("archive" + URLEXT, template.render(entries=f))

@step
def generate_colophon(f, e):
    """Generate a colophon page"""
    template = e.get_template(TEMPLATES['colophon'])
    write_file("colophon" + URLEXT, template.render(entries=f))

@step
def generate_404(f, e):
    """Generate a 404 page"""
    template = e.get_template(TEMPLATES['404'])
    write_file("404" + URLEXT, template.render(entries=f))

@step
def detail_pages(f, e):
    """Generate detail pages of individual posts"""
    template = e.get_template(TEMPLATES['detail'])
    for file in f:
        write_file(file['url'], template.render(entry=file))

def main():
    print "Chiseling..."
    print "\tReading files...",
    files = sorted(get_tree(source_path), cmp=compare_entries)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH), **TEMPLATE_OPTIONS)
    print "Done."
    print "\tRunning steps..."
    for step in STEPS:
        print "\t\t",
        step(files, env)
    print "\tDone."
    print "Done."

if __name__ == "__main__":
    sys.exit(main())
