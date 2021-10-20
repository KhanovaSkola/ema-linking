#!/usr/bin/env python3
import json
from tsv_reader import TsvContentReader

# This is a one time skript to effectively map KSID
# of already linked content, which was originally linked to KS
# and hence indexed via KS ID.

# This concerns only two json files:
#   ks_obecna_chemie_video.json
#   ks_organicka_chemie_video.json

# The goal here is to use the KA_URL in those JSON files
# and map them to the corresponding KA ID (inverse map read from TSV content
# file). Then we re-print the JSON again, with the KSID swapped to KAID.
# This json file is NOT supposed to be uploaded to EMA!
# Instead, it will be then read by 'ka_content_linking.py'
# to skip videos that are already linked to EMA.

OBECNA_CHEMIE_KS = 'ks_obecna_chemie_video_new.json'
ORGANICKA_CHEMIE_KS = 'ks_organicka_chemie_video_new.json'

TSV_CONTENT_FILE_CS = 'tsv_download.cs.tsv'
# NOTE: The 'ka_' at the begging is important!
OUTPUT_MAP_FILE = 'existing-links/ka_ks_chemie_video_reindexed.json'

tsv = TsvContentReader(TSV_CONTENT_FILE_CS)
ka_cs_vid = tsv.get_content('video', 'science')

nodeslug_kaid_map = {
    v['node_slug']: v['id'] for v in ka_cs_vid
}

linked_content = []

with open(OBECNA_CHEMIE_KS, "r") as f:
    ks_json = json.loads(f.read())

for v in ks_json:
    slug = v['url'].split('/v/')[1]
    node_slug = 'v/' + slug
    ka_id = nodeslug_kaid_map[node_slug]
    item = v.copy()
    item['id'] = ka_id
    linked_content.append(item)

with open(ORGANICKA_CHEMIE_KS, "r") as f:
    ks_json = json.loads(f.read())

for v in ks_json:
    slug = v['url'].split('/v/')[1]
    node_slug = 'v/' + slug
    ka_id = nodeslug_kaid_map[node_slug]
    item = v.copy()
    item['id'] = ka_id
    linked_content.append(item)

with open(OUTPUT_MAP_FILE, 'w', encoding='utf-8') as f:
    f.write(json.dumps(linked_content, ensure_ascii=False, allow_nan=False, indent=4, sort_keys=True))

print('Number of videos:', len(linked_content))
