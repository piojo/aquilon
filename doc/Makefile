DOCBOOK_VERSION = 5.0
DOCBOOK_XSL_VERSION = 1.77.1
LIBXSLT_VERSION = 1.1.26-2.7.8-z1.2a
LIBXML_VERSION = 2.7.8

DOCBOOK = /ms/dist/fsf/PROJ/docbook/$(DOCBOOK_VERSION)
DOCBOOK_XSL = /ms/dist/fsf/PROJ/docbook-xsl-ns/$(DOCBOOK_XSL_VERSION)/common

XSLTPROC = /ms/dist/gnome/PROJ/libxslt/$(LIBXSLT_VERSION)/exec/bin/xsltproc
XSLT_PARAMS = --xinclude --nonet --catalogs

XMLLINT = /ms/dist/gnome/PROJ/libxml/$(LIBXML_VERSION)/exec/bin/xmllint
# For DocBook 5, the normative description is the Relax NG schema
XMLLINT_PARAMS = --xinclude --nonet --catalogs --noout --relaxng $(DOCBOOK)/rng/docbook.rng

# Used by xsltproc & xmllint to convert URIs to file names
SGML_CATALOG_FILES = $(DOCBOOK)/catalog.xml
export SGML_CATALOG_FILES

FORMATS = man html

COMMAND_SOURCES = $(wildcard commands/*.xml)
ALL_SOURCES = $(wildcard *.xml) $(COMMAND_SOURCES)
GENERATED_XML = common/cluster_location_options.xml common/member_location_options.xml

MAN_OUTPUT = $(addprefix man/man1/aq_,$(notdir $(COMMAND_SOURCES:.xml=.1)))

# Eventually we'll want to add other items to HTML_OUTPUT...
HTML_OUTPUT = $(addprefix html/aq_,$(notdir $(COMMAND_SOURCES:.xml=.html)))

all: version.txt $(FORMATS)

common/cluster_location_options.xml: generate_locations.xsl common/location_options.xml
	$(XSLTPROC) --stringparam location_type cluster $^ > $@

common/member_location_options.xml: generate_locations.xsl common/location_options.xml
	$(XSLTPROC) --stringparam location_type member $^ > $@

man: $(MAN_OUTPUT)

$(MAN_OUTPUT): $(COMMAND_SOURCES) $(GENERATED_XML) version.txt
	$(XSLTPROC) $(XSLT_PARAMS) style-man.xsl $(COMMAND_SOURCES)

html: $(HTML_OUTPUT)

$(HTML_OUTPUT): $(ALL_SOURCES) $(GENERATED_XML) version.txt
	$(XSLTPROC) $(XSLT_PARAMS) style-html.xsl $(ALL_SOURCES)

version.txt: FORCE
	@# We don't want the -rc suffix to show up in the man pages
	@git describe 2>/dev/null | sed -e 's/-rc[0-9]\+$$//' > $@.tmp
	@# Don't force a full rebuild unless the version has changed
	@cmp -s $@ $@.tmp; if [ $$? -gt 0 -a -s $@.tmp ]; then mv $@.tmp $@; else rm -f $@.tmp; fi

clean:
	-rm -rf html
	-rm -rf man
	-rm -f version.txt
	-rm -f $(GENERATED_XML)

install-man: man
	for file in `find man -type f`; do \
		install -m 644 -D "$$file" "$(DESTDIR)/$$file"; \
	done

install-html: html
	for file in `find html -type f`; do \
		install -m 644 -D "$$file" "$(DESTDIR)/$$file"; \
	done

install: all install-man install-html

# Use "make check" to validate the XML files. Unfortunately the error
# messages can be misleading sometimes...
check: version.txt $(GENERATED_XML)
	$(XMLLINT) $(XMLLINT_PARAMS) $(ALL_SOURCES)
	@./check_command_options.py

.PHONY: all check clean install install-man install-html man html FORCE
