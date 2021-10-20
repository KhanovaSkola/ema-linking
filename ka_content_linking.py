#!/usr/bin/env python3
import argparse, sys
import time, re, json
from pprint import pprint

from tsv_reader import TsvContentReader

# 1. Read all already existing JSON files to prevent duplicates
# 2. For that we're going to need maping from KS-ID to KA-ID
# 3. For already existing JSON files, we want to preserve the KS-ID,
#    but change URL to CS-KS
# 4. Figure out what is the best structure for the data
#     - the smalled unit is probably course, identified by its slug
#     - for now only link exercises and videos

def read_cmd():
   """Reading command line options."""
   desc = "Program for linking CS-Khan content for EMA-RVP database."
   parser = argparse.ArgumentParser(description=desc)
   parser.add_argument('-D','--domain', dest='domain', default = 'root', help = 'Link given course.')
   parser.add_argument('-c','--content', dest='content', required = True, help = 'Content kind: video|exercise')
   parser.add_argument('-d','--debug', dest = 'debug', action = 'store_true', help = 'Print all available courses')
   return parser.parse_args()

# Currently, article type does not seem to work.
CONTENT_TYPES = ['video', 'exercise', 'article']
TSV_CONTENT_FILE = 'tsv_download.cs.tsv'

EMA_OPTIONAL_DATA = {
    'jazyk': '5-cs',
    'autor': 'Khan Academy',
    'dostupnost': '7-ANO', # OER
    'typ': {
        'video': '8-VI',
        'exercise': '8-IC',
        'article': '8-CL'
    },
    'licence': {
        'cc-by-nc-nd': '1-CCBYNCND30',
        'cc-by-nc-sa': '1-CCBYNCSA30',
        'cc-by-sa': '1-CCBYSA30',
        'yt-standard': '1-OST'
    },
    'stupen_vzdelavani': {
        'early-math': '2-Z',
        'arithmetic': '2-Z',
        'pre-algebra': '2-Z',
        'basic-geo': '2-Z',
        'algebra-basics': '2-Z',
        'trigonometry': '2-G',
        'fyzika-mechanika': '2-G',
        'fyzika-elektrina-a-magnetismus': '2-G',
        'fyzika-vlneni-a-zvuk': '2-G',
        'fyzika-vlneni-a-zvuk': '2-G',
        'obecna-chemie': '2-G',
        'fyzikalni-chemie': '2-G',
        'organic-chemistry': '2-G',
        'biology': '2-G',
        'music': '2-NU',
        'cosmology-and-astronomy': '2-NU'
    },
    'vzdelavaci_obor': {
        'math': '9-03',
        'music': '9-11',
        'physics': '9-07',
        'chemistry': '9-08',
        'biology': '9-09',
        'astro': '9-09', # TODO: 9-10' # Not clear whether we can have multiple types
    },
    'rocnik': {
        'early-math': '3-Z13',
        'trigonometry': '3-SS',
        'fyzika-mechanika': '3-SS',
        'fyzika-elektrina-a-magnetismus': '3-SS',
        'fyzika-vlneni-a-zvuk': '3-SS',
        'obecna-chemie': '3-SS',
        'fyzikalni-chemie': '3-SS',
        'organic-chemistry': '3-SS',
        'fyzika-vlneni-a-zvuk': '3-SS',
        'biology': '3-SS',
    },
    'gramotnost': {
        'math': '4-MA',
        'music': '4-NU',
        'astro': '4-PR',
        'physics': '4-PR',
        'chemistry': '4-PR',
        'biology': '4-PR',
    }
}

COURSE_SUBJECT_MAP = {
    'music': 'music',
    'cosmology-and-astronomy': 'astro',
    'early-math': 'math',
    'arithmetic': 'math',
    'basic-geo': 'math',
    'algebra-basics': 'math',
    'pre-algebra': 'math',
    'trigonometry': 'math',
    'fyzika-mechanika': 'physics',
    'fyzika-elektrina-a-magnetismus': 'physics',
    'fyzika-vlneni-a-zvuk': 'physics',
    'obecna-chemie': 'chemistry',
    'organic-chemistry': 'chemistry',
    'fyzikalni-chemie': 'chemistry',
    'biology': 'biology',
}

def read_existing_links():
    """Read all existing links in pre-existing EMA JSON files"""
    # TODO: Iterate over all JSON file 'ka_*.json' in this dir
    # to filter out duplicates in Math courses as well.
    DIR = 'existing-links/'
    with open('existing-links/ka_ks_chemie_video_reindexed.json', 'r') as f:
        ema_links = json.loads(f.read())

    existing_ids = set(v['id'] for v in ema_links)
    return existing_ids

def strip_html_stuff(string):
    strout = re.sub('<[^<]+?>', '', string)
    strout = strout.replace(
            '&nbsp;', ' ').replace(
            '&quot;', "'").replace(
            '&Delta;', 'Δ').replace(
            '&rarr;', '→').replace(
            '&oslash;', 'ø').replace(
            '&ouml;', 'ö').replace(
            '&#39;', "'")
    return strout


def ema_print_domain_content(content, content_type, courses, fname):
    ema_content = []
    existing_ids = read_existing_links()
    unique_content_ids = existing_ids

    for v in content:

        course = v['course']
        # Only print content from a selected list of courses
        if course not in courses:
            continue

        subject = COURSE_SUBJECT_MAP[course]

        if v['id'] in unique_content_ids:
            if opts.debug:
                print('slug is already linked' % v['node_slug'])
            continue
        else:
            unique_content_ids.add(v['id'])

        # Skip unlisted content
        if not v['listed']:
            continue

        desc = v['translated_description']

        # If a description does not exist, let's use Title as an ugly hack
        if desc is None or not desc:
            if opts.debug:
                print(v['id'], 'WARNING: Empty description, returning None')
            desc = v['translated_title']

        desc = strip_html_stuff(desc)

        try:
          item = {
            # Mandatory items
            'id': v['id'],
            'url': v['url'],
            'nazev': v['translated_title'],
            'popis': desc,
            # Constant items
            'autor': EMA_OPTIONAL_DATA['autor'],
            'jazyk': EMA_OPTIONAL_DATA['jazyk'],
            'dostupnost': EMA_OPTIONAL_DATA['dostupnost'],
            # Optional fields
            'typ': EMA_OPTIONAL_DATA['typ'][content_type],
            'stupen_vzdelavani': EMA_OPTIONAL_DATA['stupen_vzdelavani'][course],
            'vzdelavaci_obor': EMA_OPTIONAL_DATA['vzdelavaci_obor'][subject],
            'gramotnost': EMA_OPTIONAL_DATA['gramotnost'][subject],
            # TODO: Creation date might not make sense...
#            'datum_vzniku': v['creation_date']
            # KA API gives keywords in EN, commenting out for now....
#            'klicova_slova': v['keywords'],
#            'otevreny_zdroj': '7-ANO',
          }

          # Do not export empty fieds...
          # TODO: should make this more general
          if course in EMA_OPTIONAL_DATA['rocnik'].keys() and EMA_OPTIONAL_DATA['rocnik'][course] != '':
              item['rocnik'] = EMA_OPTIONAL_DATA['rocnik'][course]

          # TODO: Refactor this, it is confusing
          if 'ka_user_licence' in v.keys():
             item['licence'] = EMA_OPTIONAL_DATA['licence'][v['ka_user_license']]
          else:
             item['licence'] = EMA_OPTIONAL_DATA['licence']['cc-by-nc-sa'] # Let's just take the KA default

          if item['licence'] == '1-OST':
              if v['ka_user_licence'] == 'yt-standard':
                item['licence_url'] = 'https://www.youtube.com/static?template=terms&gl=CZ'
              else:
                if opts.debug:
                    eprint("WARNING: Missing license URL!")
                del item['licence']

          ema_content.append(item)

        except KeyError:
            print('Key error! Content item:')
            pprint(v)
            raise
 
    with open(fname, 'w', encoding = 'utf-8') as f:
        f.write(json.dumps(ema_content, ensure_ascii=False, allow_nan=False, indent=4, sort_keys=True))

    print('Number of EMA %ss = %d' % (content_type, len(ema_content)))


if __name__ == '__main__':

    opts = read_cmd()
    domain = opts.domain
    content_type = opts.content.lower()

    if content_type not in CONTENT_TYPES:
        print("ERROR: invalid content types: ", opts.content)
        print("Available content types: ", CONTENT_TYPES)
        exit(1)

    # TODO: Add all math courses
    math_courses = set(['early-math', 'arithmetic', 'basic-geo', 'trigonometry',
            'algebra-basics', 'pre-algebra'])

    science_courses = set(['fyzikalni-chemie'])
    science_courses = set(['fyzika-mechanika', 'fyzika-elektrina-a-magnetismus',
            'fyzika-vlneni-a-zvuk', 'obecna-chemie', 'fyzikalni-chemie',
            'organic-chemistry', 'biology'])

    # TODO: Add other domains?
    domain_courses_map = {
            "math": math_courses,
            "science": science_courses
            }

    tsv = TsvContentReader(TSV_CONTENT_FILE)
    content = tsv.get_content(content_type, domain)
    out_fname = 'ka_%s_%s.json' % (domain, content_type)

    courses = domain_courses_map[domain]

    ema_print_domain_content(content, content_type, courses, out_fname)

