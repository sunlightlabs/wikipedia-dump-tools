#!/bin/bash

bindir=$(dirname $(readlink -f "$0"))
cmd=$(basename $(readlink -f "$0")) 

if [ -z "$1" ]; then
    echo
    echo "Utility to extract the <page>...</page> for the given"
    echo "document id from the wikipedia dump file."
    echo
    echo "USAGE: $cmd DOCUMENT_ID"
    echo
    exit 1
fi

python -m wikitools.pageprocessor --log /dev/null \
                                  --loglevel warning \
                                  --continue-on-error "$bindir/enwiki-latest-pages-articles.xml.bz2" \
                                  wikitools.examples.stop_at_document["$1"] \
                                  wikitools.examples.echo_dom \
                                  wikitools.examples.only_document["$1"] > "$1".xml

cat "$1".xml
ls -lh "$1".xml
