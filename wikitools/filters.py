# -*- coding: utf-8 -*-

from __future__ import division, print_function

from wikitools import DropPage

__all__ = ['minimum_text_length', 'limit_to_namespace', 'limit_to_format',
           'drop_redirects', 'drop_disambiguation_pages', 'drop_listof_pages']

def minimum_text_length(minchars, page_dom):
    elems = page_dom.xpath('/page/revision/text')
    if len(elems) == 0:
        raise DropPage(page_dom, u"no text element")

    if elems[0].text is None:
        raise DropPage(page_dom, u"empty text element")

    textlen = len(elems[0].text)
    if textlen < minchars:
        raise DropPage(page_dom, u"text shorter than {0} characters".format(minchars))

    return page_dom

def limit_to_namespace(req_ns, page_dom):
    ns_elem = page_dom.find('ns')
    if ns_elem is None or ns_elem.text is None:
        raise DropPage(page_dom, u"no namespace")

    page_ns = int(ns_elem.text)
    if page_ns != req_ns:
        raise DropPage(page_dom, u"in namespace {n}".format(n=req_ns))

    return page_dom

def limit_to_format(req_fmt, page_dom):
    elems = page_dom.xpath('/page/revision/format')
    if len(elems) == 0:
        raise DropPage(page_dom, u"no format tag")

    fmt = elems[0].text
    if fmt is None:
        raise DropPage(page_dom, u"empty format tag")

    if fmt != req_fmt:
        raise DropPage(page_dom, u"wrong format: {0} is not {1}".format(fmt, req_fmt))

    return page_dom

def drop_redirects(page_dom):
    if page_dom is not None:
        redirect_elem = page_dom.find('redirect')
        if redirect_elem is not None:
            raise DropPage(page_dom, u"redirects to {t}".format(t=redirect_elem.attrib['title']))
    return page_dom

def drop_disambiguation_pages(page_dom):
    title_elem = page_dom.find('title')
    if title_elem is not None and title_elem.text.endswith(u' (disambiguation)'):
        raise DropPage(page_dom, u"is a disambiguation page")
    return page_dom

def drop_listof_pages(page_dom):
    title_elem = page_dom.find('title')
    if title_elem is not None and u'List of ' in title_elem.text:
        raise DropPage(page_dom, u"is a list page")
    return page_dom

def text_contains(needle, page_dom):
    revision_elem = page_dom.find('revision')
    if revision_elem is None:
        return page_dom
    text_elem = revision_elem.find('text')
    if text_elem is None:
        return page_dom
    if text_elem.text is None:
        return page_dom
    if needle in text_elem.text:
        return page_dom
    raise DropPage(page_dom, u"Does not contain {}".format(needle))

