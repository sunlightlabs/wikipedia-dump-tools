# -*- coding: utf-8 -*-

__all__ = ['DropPage']

class NoneAttrs(object):
    def __getattr__(self, attr):
        return None

def xpath_single(doc, expr):
    results = doc.xpath(expr)
    if len(results) == 0:
        return NoneAttrs()
    else:
        return results[0]

class DropPage(Exception):
    def __init__(self, document, reason, *args, **kwargs):
        doc_id = xpath_single(document, '/page/id').text
        doc_title = xpath_single(document, '/page/title').text
        msg = u"Dropped document #{id} '{t}': {r}".format(id=doc_id,
                                                          t=doc_title,
                                                          r=unicode(reason))
        super(DropPage, self).__init__(msg, *args, **kwargs)

