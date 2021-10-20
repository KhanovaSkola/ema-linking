#!/usr/bin/env python3
# coding: utf-8

import argparse
from sys import exit
import json

# A short one-time script that redirects existing KS links in EMA
# to CS-KA. Currently only needed for ks_organicka_chemie_video.json
# and ks_obecna_chemie_video.json

# Note that we will DELETE links to old videos
# that do not have equivalent on CS-KA.

def read_cmd():
   desc = "Program for linking CS-Khan content for EMA reputation system."
   parser = argparse.ArgumentParser()
   parser.add_argument('json_file',help='JSON file containing EMA links to KS')
   return parser.parse_args()

def print_hashes():
    print('##########################################')

#KSID_KAURL_MAP_FILE = 'ksid_kaurl_09-2021.tsv'
KSID_KAURL_MAP_FILE = 'ksid_kaurl_19-10-2021.tsv'

if __name__ == '__main__':

    opts = read_cmd()

    ksid_kaurl = {}

    print("Reading file", KSID_KAURL_MAP_FILE)
    with open(KSID_KAURL_MAP_FILE, 'r') as f:
        for line in f:
            l = line.split('\t')
            ksid = int(l[0])
            kaurl = l[1].rstrip()
            ksid_kaurl[ksid] = kaurl

    print('number of KA URLs on KS = ', len(ksid_kaurl))

    print("\nReading file", opts.json_file)
    with open(opts.json_file, 'r', encoding='utf-8') as f:
        ema_links = json.loads(f.read())

        print('Number of EMA LINKS', len(ema_links))

    new_links = []
    print("\nRemoving following content")
    print_hashes()
    for link in ema_links:
        if link['id'] in ksid_kaurl.keys():
            link['url'] = ksid_kaurl[link['id']]
            new_links.append(link)
        else:
            print(link['nazev'])

    print_hashes()
    print("\nNumber of new links", len(new_links))
    print("Printing new JSON file to content.json")

    with open('content.json', "w", encoding='utf-8') as f:
        f.write(json.dumps(new_links, ensure_ascii=False, allow_nan=False, indent=4, sort_keys=True))
