# -*- coding: utf-8 -*-

from __future__ import division, print_function

import sys
import logging
import random
import lxml.etree

from wikitools.exceptions import DropPage, AbortProcess

def raise_exception(page_dom):
    raise Exception("Test exception")

def echo_dom(page_dom):
    print(lxml.etree.tostring(page_dom))
    return page_dom

def sample_five_percent(page_dom):
    rnd = random.random()
    if rnd >= 0.05:
        raise DropPage(page_dom, "{} > 0.05".format(rnd))
    return page_dom

def require_line_breaks(page_dom):
    elem = page_dom
    for tag in ['revision', 'text']:
        elem = elem.find(tag)
        if elem is None:
            raise DropPage(page_dom, u"No <{}> element".format(tag))

    doc_id = page_dom.find('id').text

    cnt = elem.text.count(u'\n')
    logging.info("{cnt} line breaks in document {doc}".format(cnt=cnt,
                                                              doc=doc_id))
    if cnt == 0:
        raise DropPage(page_dom, u"No line breaks")

    return page_dom

DocumentList = None
def only_documents_in_list(filepath, page_dom):
    global DocumentList
    if DocumentList is None:
        with file(filepath, 'rU') as infil:
            DocumentList = [int(ln1)
                            for ln1 in (ln.strip()
                                        for ln in infil.readlines())
                            if len(ln1) > 0]
    page_docid = int(page_dom.find('id').text)
    if page_docid in DocumentList:
        return page_dom
    else:
        raise DropPage(page_dom, "Document not in list.")

def only_document(docid, page_dom):
    page_docid = int(page_dom.find('id').text)
    if docid == page_docid:
        return page_dom
    elif docid < page_docid:
        raise AbortProcess("No such document: {}".format(docid))
    else:
        raise DropPage(page_dom, "Not document {}".format(docid))

def stop_at_document(docid, page_dom):
    page_docid = int(page_dom.find('id').text)
    if docid == page_docid:
        raise AbortProcess("Found")
    return page_dom

def print_text(page_dom):
    print(page_dom.find('revision').find('text').text)
    return page_dom

def print_text_for_xpath(xpath_expr, page_dom):
    results = page_dom.xpath(xpath_expr)
    if len(results) > 0:
        print(results[0].text.encode('utf-8'))
    return page_dom

