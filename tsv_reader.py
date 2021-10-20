#!/usr/bin/env python
# coding: utf-8

import sys

class TsvContentReader():
    """A class for reading Khan Academy content from a TSV file"""

    # Columns that we're actually interested in
    CONTENT_FIELDS = {
            'kind': 0,
            'node_slug': 3,
            'translated_title': 26,
            'id': 2,
            'domain': 4,
            'course': 5,
            'url': 9,
            'listed': 11,
            'translated_description': 13,
            'license': 18,
    }

    # Other kinds are ignored / not supported
    KINDS = ("video", "exercise", "article")

    def __init__(self, tsv_fname):
        self.content = self.read_tsv_content(tsv_fname)

    def get_content(self, content_kind, domain):
        if content_kind not in self.KINDS:
            print('ERROR:Kind "%s" not supported' % content_kind)
            sys.exit(1)
        if domain not in self.content[content_kind].keys():
            print('ERROR: Domain %s not found' % domain)
            sys.exit(1)
        return self.content[content_kind][domain]

    def deserialize_content_line(self, content_line):
        content_item = {}
        l = content_line.split("\t")
        for key in self.CONTENT_FIELDS:
            content_item[key] = l[self.CONTENT_FIELDS[key]]

        content_item['kind'] = content_item['kind'].lower()
        if content_item['listed'] == "True":
            content_item['listed'] = True
        else:
            content_item["listed"] = False
        return content_item

    def read_tsv_content(self, tsv_fname):
        content = {}
        for kind in self.KINDS:
            content[kind] = {}

        with open(tsv_fname, "r") as f:
            # Get rid of the header in the first line
            header = f.readline()
            for line in f:
                item = self.deserialize_content_line(line)

                if item['kind'] not in self.KINDS:
                    continue

                try:
                    content[item['kind']][item['domain']].append(item)
                except KeyError:
                    content[item['kind']][item['domain']] = [item]

        return content
