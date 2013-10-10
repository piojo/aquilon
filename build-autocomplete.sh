#!/bin/bash
python bootstrap/gen_completion.py --all
make -C doc XSLT_PARAMS='--xinclude --catalogs' \
    XMLLINT_PARAMS='--xinclude --catalogs --noout --relaxng $(DOCBOOK)/rng/docbook.rng' \
    XSLTPROC=/usr/bin/xsltproc \
    DOCBOOK_XSL=/usr/share/sgml/docbook/xsl-stylesheets/ \
    STYLE_VARIANT='-rh'
