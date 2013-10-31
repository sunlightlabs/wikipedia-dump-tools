Here you will find tools for making use of the monthly [XML dumps of Wikipedia](http://en.wikipedia.org/wiki/Wikipedia:Database_download). It is based on [WikiExtractor.py](http://medialab.di.unipi.it/Project/SemaWiki/Tools/WikiExtractor.py) from the Tanl package. Both packages address the challenge of incrementally processing <page> elements from the compressed .xml.bz2 file. While WikiExtractor.py extracts plain-text versions of the pages into smaller files for later processing, this package allows you to specify your own filtering and transformations to be run during extraction.

To specify a page filter or transformation you simply name one or more fully qualified python function "paths" on the commange line. Each page is passed (as an lxml.etree Element) to each function in the series from last to first.

```bash
    $ python -m wikitools.pageprocessor --help
    usage: pageprocessor.py [-h] [--debug-composition] [--continue-on-error]
                            [--log FILE] [--loglevel LEVEL]
                            wikipedia_archive pkg_mod_func [pkg_mod_func ...]

    Pass each page to a given function.

    positional arguments:
      wikipedia_archive    Path to the .xml.bz2 Wikipedia archive.
      pkg_mod_func         Function(s) to pass each page to, e.g.
                       wikitools.examples.print_page

    optional arguments:
      -h, --help           show this help message and exit
      --debug-composition  Dump the document after each function.
      --continue-on-error  Continue when an exception goes uncaught.
      --log FILE           Where to write the log file.
      --loglevel LEVEL     Logging level (default: info)
```

Here is an example invocation:

```bash
    $ python -m wikitools.pageprocessor enwiki-latest-pages-articles.xml.bz2 wikitools.examples.echo_dom wikitools.filters.limit_to_namespace[0] wikitools.filters.drop_redirects
```

With this invocation, each page will be passed to a function that is the equivalent of:

```python
    echo_dom(limit_to_namespace(0, drop_redirects(page_dom)))
```

Both `limit_to_namespace` and `drop_redirects` will raise a special exception `wikitools.exceptions.DropPage` in order to prevent the page from being passed to the outer functions. The use of `limit_to_namespace` differs from `drop_redirects` in that it is called with a static first argument `0`. Each function specified on the command line can be followed by a list of arguments. These arguments are the same for each invocation of the function. Specifying python literals in a shell can be awkward. Consider this example:

```python
    &#x0023 my_module.py
    def list_pages_with_prefix(prefix, page_dom):
        title = page_dom.find('title').text
        if title.startswith(prefix):
            return page_dom
        else:
            raise DropPage(page_dom, "does not start with {}".format(prefix))
```

Here's the bash invocation:

```bash
    my_module.list_pages_with_prefix['"Anti"']
```

Since bash will treat quotes specially, we need to escape them or double-quote them. If we didn't, the python process would try to evaluate `Anti` as an identifier and fail.


