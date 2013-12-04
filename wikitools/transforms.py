# -*- coding: utf-8 -*-

from __future__ import division, print_function

import re
import sys
import datetime
import urllib

from HTMLParser import HTMLParser

import lxml.etree
import inflect
words = inflect.engine()


__all__ = ['convert_to_plain_text']

RELeftSingleQuotes = re.compile(ur'[\u2018\u201B]', re.UNICODE)
RERightSingleQuotes = re.compile(ur'[\u2019\u201A]', re.UNICODE)
RELeftDoubleQuotes = re.compile(ur'[\u201C\u201F]', re.UNICODE)
RERightDoubleQuotes = re.compile(ur'[\u201D]', re.UNICODE)
def standardize_quotes(text, leftsnglquot="'", rightsnglquot="'", leftdblquot='"', rightdblquot='"'):
    """Replaces fancy quotes from unicode, latin1, and windows-1252, defaulting to ascii quotes."""
    newtext = RELeftSingleQuotes.sub(leftsnglquot, text)
    newtext = RERightSingleQuotes.sub(rightsnglquot, newtext)
    newtext = RELeftDoubleQuotes.sub(leftdblquot, newtext)
    newtext = RERightDoubleQuotes.sub(rightdblquot, newtext)
    return newtext

GarbageTags = ('ref', 'gallery', 'timeline', 'noinclude', 'pre', 'table', 'tr', 'td',
               'ul', 'li', 'ol', 'dl', 'dt', 'dd', 'menu', 'dir')
GarbagePatterns = ( [ re.compile(r'<\s*%s(\s*| [^/]+?)>.*?<\s*/\s*%s\s*>' % (tag, tag), re.DOTALL | re.IGNORECASE)
                      for tag in GarbageTags ] +
                    [ re.compile(r'<\s*%s(\s*| [^/]+?)\s*/>' % (tag, ), re.DOTALL | re.IGNORECASE)
                      for tag in GarbageTags ] )
def remove_garbage_tags(text):
    for pattern in GarbagePatterns:
        text = pattern.sub('', text)
    return text


def drop_postlude(text):
    return re.compile(ur'^[=]+\s*(External [Ll]inks|See [Aa]lso|(Further|Additional) [Rr]eading|References|Bibliography|Notes)\s*[=]+\s*$.*', re.M | re.DOTALL).sub('', text)


CONDENSE_WHITESPACE = re.compile(ur'[^\S\n]+', re.UNICODE)
CONDENSE_NEWLINES = re.compile(ur'\s*\n+\s*', re.UNICODE)
REMOVE_SINGLE_NEWLINE = re.compile(ur'([^\n\r])(\r\n|\n\r|\r|\n)([^*\r\n])', re.UNICODE | re.M)
def condense_whitespace(string):
    # collapse single newlines into none
    string = re.sub(REMOVE_SINGLE_NEWLINE, ur'\1 \3', string)

    # condense all whitespace (except newlines) to a single space
    string = re.sub(CONDENSE_WHITESPACE, u' ', string)

    # combine multiple newlines into one
    string = re.sub(CONDENSE_NEWLINES, u'\n', string)

    return string

def expand_linebreaks(string):
    return re.compile(ur'[\r\n]', re.U | re.M).sub(u'\n\n', string)

def repeatedly_strip_pattern(pattern, text):
    textlen = 0
    while len(text) != textlen and len(text) > 0:
        textlen = len(text)
        text = pattern.sub('', text)
    return text

MVarTemplatePattern = re.compile(ur'{{mvar\|([a-z]+)}}', re.I | re.M)
def expand_mvar_templates(text):
    return MVarTemplatePattern.sub(ur'\1', text)

# \u2212 = −
ConvertTemplatePattern = re.compile(ur'({{convert\|(\\u[0-9]+?|[-\u2212.,0-9]+?)\|(.+?)(\|.+?)?}})', re.I | re.M)
def expand_convert_templates(text):
    unit_phrases = {
        # This dict excludes degrees because they do not need to be expanded.
        u'g': u'gram',
        u'kg': u'kilogram',

        u'lb': u'pound',
        u'Moilbbl': u'million barrel',

        u'mm': u'millimeter',
        u'cm': u'centimeter',
        u'm': u'meter',
        u'km': u'kilometer',
        u'km2': u'square kilometer',
        u'sqkm': u'square kilometer',

        u'in': u'inch',
        u'ft': u'foot',
        u'mi': u'mile',
        u'mi2': u'square mile',
        u'sqmi': u'square mile',
        u'nmi': u'nautical mile',

        u'ha': u'hectare',
        u'e6acre': u'million acre',
        u'e6ha': u'million hectare'
    }
    matches = ConvertTemplatePattern.findall(text)
    for (match_text, value, unit, _) in matches:
        if unit in unit_phrases:
            unit = unit_phrases[unit]
            if value != u'1':
                unit = words.plural(unit)
        text = text.replace(match_text, u"{0} {1}".format(value, unit))
    return text

NihongoTemplatePattern = re.compile(ur"({{nihongo\|(.+?)}})", re.M)
def expand_nihongo_templates(text):

    def _expand_nihongo_args(args_match):
        args = args_match.split(u"|")

        args = [a.strip() for a in args if a is not None]

        primary = None
        kanji = None
        transliteration = None
        extra = []

        try:
            primary = args.pop(0)
            kanji = args.pop(0)
            transliteration = args.pop(0)
            remainder = args
        except IndexError:
            pass

        if primary is not None:
            primary = primary.strip()
        if kanji is not None:
            kanji = kanji.strip()
        if transliteration is not None:
            transliteration = transliteration.strip()

        extra = [a.replace("extra=", "").replace("extra2=", "")
                 for a in remainder
                 if a.startswith("lead=") == False]

        replacement = [primary]
        if transliteration is not None:
            replacement.append(" (")
            replacement.append(transliteration)
            if len(extra) > 0:
                replacement.append(", ")
                replacement.append(extra.pop(0))
            replacement.append(")")
        if len(extra) > 0:
            replacement.append(" ")
            replacement.append(extra.pop(0))

        return "".join(replacement)

    matches = NihongoTemplatePattern.findall(text)
    for (tmpl, args) in matches:
        text = text.replace(tmpl, _expand_nihongo_args(args))

    return text

# {{other uses}}
# [[Image:Rfel vsesmer front.png|thumb|Artificial omni-directional sound source in an [[anechoic chamber]]]]
WikiCategoryLinkPattern = re.compile(ur'^\[\[Category:.*?\]\]\s*$', re.M)
def kill_single_line_category_links(text):
    """Removes single-line category links, e.g.: [[Category:Anti-capitalism]]"""
    return WikiCategoryLinkPattern.sub(u'', text)

WikiH6Pattern = re.compile(ur'^======(.+?)======', re.M | re.UNICODE)
WikiH5Pattern = re.compile(ur'^=====(.+?)=====', re.M | re.UNICODE)
WikiH4Pattern = re.compile(ur'^====(.+?)====', re.M | re.UNICODE)
WikiH3Pattern = re.compile(ur'^===(.+?)===', re.M | re.UNICODE)
WikiH2Pattern = re.compile(ur'^==(.+?)==', re.M | re.UNICODE)
WikiH1Pattern = re.compile(ur'^=(.+?)=', re.M | re.UNICODE)
def simplify_headings(text):
    text = WikiH6Pattern.sub(ur'\n\1\n', text)
    text = WikiH5Pattern.sub(ur'\n\1\n', text)
    text = WikiH4Pattern.sub(ur'\n\1\n', text)
    text = WikiH3Pattern.sub(ur'\n\1\n', text)
    text = WikiH2Pattern.sub(ur'\n\1\n', text)
    text = WikiH1Pattern.sub(ur'\n\1\n', text)
    return text

WikiTablePattern = re.compile(ur'[{][|]([{](?![|])|(?<![{])[|]|[^{|])*?[|][}]', re.M | re.S)
WikiTemplatePattern = re.compile(ur'{{[^{]+?}}', re.M)
WikiBoldPattern = re.compile(ur"\'\'\'(.+?)\'\'\'", re.M)
WikiItalicsPattern = re.compile(ur"\'\'(.+?)\'\'", re.M)
WikiTOCPattern = re.compile(ur'__(NOTOC|FORCETOC|TOC)__')
WikiIndentationPattern = re.compile(ur'^:+', re.M)
WikiHRulePattern = re.compile(ur'^\s*[-]{4,}\s*$', re.M)
WikiFileOrImageLinkPattern = re.compile(ur'\[\[(File|Image):[^[]+?\]\]', re.M)
HtmlCommentPattern = re.compile(ur'<!--.*?-->', re.M | re.DOTALL)
WiktionaryLinkPattern = re.compile(ur'\[\[(?:wikt|Wiktionary):(.*?)\|(.*?)\]\]', re.M)
ExternalLinkPattern = re.compile(ur'\[http://\S+ (.*?)\]', re.M)
EmptyListItemPattern = re.compile(ur'^\*\s*$', re.M)
# The first set of internal link patterns are required to avoid matching
# File, Image:, etc. We handle those separately and then reduce internal links again.
InternalLinkPatternFull1 = re.compile(ur'\[\[([^:\|\[]+?)\|([^\[]+?)\]\]', re.M)
InternalLinkPatternSimple1 = re.compile(ur'\[\[([^:\|\[]+?)\]\]', re.M)
InternalLinkPatternFull2 = re.compile(ur'\[\[([^\[]+?)\|([^\[]+?)\]\]', re.M)
InternalLinkPatternSimple2 = re.compile(ur'\[\[([^\[]+?)\]\]', re.M)
# A common pattern is "Some noun ({{some template}}) blah blah" which, after
# stripping out most templates yields "Some noun () blah blah". This pattern
# is used to strip out the empty parentheses.
EmptyParenthesesPattern = re.compile(ur'\s+\(\s*\)\s+', re.M)
def convert_to_plain_text(page_dom):
    text_elem = page_dom.find('revision').find('text')
    text = text_elem.text

    text = HTMLParser().unescape(text)
    text = remove_garbage_tags(text)
    text = drop_postlude(text)
    text = WikiTOCPattern.sub(u'', text)
    text = simplify_headings(text)
    text = expand_nihongo_templates(text)
    text = WikiBoldPattern.sub('\\1', text)
    text = WikiItalicsPattern.sub('\\1', text)
    # TODO: Consider replacing with \u00a0, \u2005, or \u2009
    text = WikiIndentationPattern.sub(u'', text)
    text = expand_convert_templates(text)
    text = expand_mvar_templates(text)
    text = WikiHRulePattern.sub(u'', text)
    text = repeatedly_strip_pattern(WikiTemplatePattern, text)

    text = InternalLinkPatternSimple1.sub(u'\\1', text)
    text = InternalLinkPatternFull1.sub(u'\\2', text)

    text = HtmlCommentPattern.sub(u'', text)
    text = kill_single_line_category_links(text)
    text = WikiFileOrImageLinkPattern.sub(u'', text)
    text = WiktionaryLinkPattern.sub(u'\\1', text)
    text = ExternalLinkPattern.sub(u'\\1', text)

    text = InternalLinkPatternSimple2.sub(u'\\1', text)
    text = InternalLinkPatternFull2.sub(u'\\2', text)

    text = repeatedly_strip_pattern(WikiTablePattern, text)

    text = EmptyListItemPattern.sub(u'', text)
    text = EmptyListItemPattern.sub(u' ', text)

    text = standardize_quotes(text)
    text = condense_whitespace(text)
    text = expand_linebreaks(text)

    text_elem.text = text
    return page_dom

if __name__ == "__main__":
    print(convert_to_plain_text(lxml.etree.parse(sys.stdin)).find('revision').find('text').text.encode('utf-8'))
