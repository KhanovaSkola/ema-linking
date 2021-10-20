#!/usr/bin/env python
# coding: utf-8

import sys

class TsvContentReader():
    """A class for reading Khan Academy content from a TSV file"""

    # Extracted from crowdin-go/scripts/content_export.py
    COLUMNS = (u'kind', u'original_title', u'id', u'slug',
               u'domain', u'course', u'unit', u'lesson',
               u'source_lang', u'canonical_url',
               u'creation_date', u'listed', u'curriculum_key',
               u'translated_description_html', u'children_ids',
               u'standards',
               # columns specific to Videos (or Talkthroughs)
               u'youtube_id', u'duration', u'license',
               u'download_urls', u'thumbnail_url',
               u'prerequisites', u'related_content',
               u'suggested_completion_criteria', u'time_estimate',
               u'assessment_item_ids')

    INTL_COLUMNS = (u'translated_title', u'translated_youtube_id', u'subbed',
                    u'dubbed', u'dub_subbed', u'word_count', u'approved_count',
                    u'translated_count', u'word_count_revised',
                    u'approved_count_revised', u'translated_count_revised',
                    u'listed_anywhere', u'fully_translated')

    # Columns that we're actually interested in
    # TODO: We need translated desc and title!
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
            print(f'ERROR:Kind "{content_kind}" not supported')
            sys.exit(1)
        if domain not in self.content[content_kind].keys():
            print(f'ERROR: Domain {domain} not found')
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

if __name__ == '__main__':
    r = TsvContentReader("tsv_download.cs.tsv")
    c = r.get_content("video", "science")
    print(len(c))
    print(c[0])
    c = r.get_content("exercise", "science")
    print(len(c))
    print(c[0])
    
