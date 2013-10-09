import random
import lxml.etree

from wikitools.exceptions import DropPage

def raise_exception(page_dom):
    raise Exception("Test exception")

def echo_dom(page_dom):
    print(lxml.etree.tostring(page_dom))

def sample_five_percent(page_dom):
    rnd = random.random()
    if rnd >= 0.05:
        raise DropPage(page_dom, "{} > 0.05".format(rnd))
    return page_dom

