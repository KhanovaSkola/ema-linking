#!/usr/bin/env python3
import argparse, sys
import time, re, json
from pprint import pprint
import glob

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
CONTENT_KINDS = ['video', 'exercise', 'article', 'topic']
TSV_CONTENT_FILE = 'tsv_download.cs.tsv'

EMA_OPTIONAL_DATA = {
    'jazyk': '5-cs',
    'autor': 'Khan Academy',
    'dostupnost': '7-ANO', # OER
    'typ': {
        'video': '8-VI',
        'exercise': '8-IC',
        'article': '8-CL',
        'topic': '8-OK',
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
        'vyrazy': '2-G',
        'funkce': '2-G',
        'analyticka-geometrie': '2-G',
        'komplexni-cisla': '2-G',
        'differential-calculus': '2-G',
        'integralni-pocet': '2-G',
        'pravdepodobnost-a-kombinatorika': '2-G',
        'posloupnosti-a-rady': '2-G',
        'fyzika-mechanika': '2-G',
        'fyzika-elektrina-a-magnetismus': '2-G',
        'fyzika-vlneni-a-zvuk': '2-G',
        'fyzika-vlneni-a-zvuk': '2-G',
        'obecna-chemie': '2-G',
        'fyzikalni-chemie': '2-G',
        'organic-chemistry': '2-G',
        'biology': '2-G',
        'music': '2-NU',
        'cosmology-and-astronomy': '2-NU',
        'informatika-pocitace-a-internet': '2-NU',
        'computer-programming': '2-NU',
        'code-org': '2-Z',
    },
    'vzdelavaci_obor': {
        'math': '9-03',
        'music': '9-11',
        'physics': '9-07',
        'chemistry': '9-08',
        'biology': '9-09',
        'computing': '9-19',
        'astro': '9-09', # TODO: 9-10' # Not clear whether we can have multiple types
    },
    'rocnik': {
        'early-math': '3-Z13',
        'trigonometry': '3-SS',
        'analyticka-geometrie': '3-SS',
        'komplexni-cisla': '3-SS',
        'differential-calculus': '3-SS',
        'integralni-pocet': '3-SS',
        'pravdepodobnost-a-kombinatorika': '3-SS',
        'posloupnosti-a-rady': '3-SS',
        'fyzika-mechanika': '3-SS',
        'fyzika-elektrina-a-magnetismus': '3-SS',
        'fyzika-vlneni-a-zvuk': '3-SS',
        'obecna-chemie': '3-SS',
        'fyzikalni-chemie': '3-SS',
        'organic-chemistry': '3-SS',
        'fyzika-vlneni-a-zvuk': '3-SS',
        'biology': '3-SS',
        'informatika-pocitace-a-internet': '3-SS',
        'computer-programming': '3-NU',
    },
    'gramotnost': {
        'math': '4-MA',
        'music': '4-NU',
        'astro': '4-PR',
        'physics': '4-PR',
        'chemistry': '4-PR',
        'biology': '4-PR',
        'computing': '4-DI',
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
    'vyrazy': 'math',
    'funkce': 'math',
    'komplexni-cisla': 'math',
    'analyticka-geometrie': 'math',
    'differential-calculus': 'math',
    'integralni-pocet': 'math',
    'pravdepodobnost-a-kombinatorika': 'math',
    'posloupnosti-a-rady': 'math',
    'pravdepodobnost-a-kombinatorika': 'math',
    'fyzika-mechanika': 'physics',
    'fyzika-elektrina-a-magnetismus': 'physics',
    'fyzika-vlneni-a-zvuk': 'physics',
    'obecna-chemie': 'chemistry',
    'organic-chemistry': 'chemistry',
    'fyzikalni-chemie': 'chemistry',
    'biology': 'biology',
    'informatika-pocitace-a-internet': 'computing',
    'computer-programming': 'computing',
    'code-org': 'computing',
}

# Filter out programming Units/Lessons that we do not want
EXCLUDED_PROGRAMING_TOPICS = (
    'browse', 'projectfeedback',
    'pjs-documentation', 'webpage-documentation', 'sql-documentation',
    'coloring', 'becoming-a-community-coder', 'resizing-with-variables',
    'side-scroller', 'programming-3d-shapes', 'advanced-development-tools',
)

def read_existing_links():
    """Read all existing links in pre-existing EMA JSON files"""
    files = [f for f in glob.glob("existing-links/ka_*.json") ]
    if len(files) == 0:
        print("ERROR: Did not find existing json files")
        sys.exit(1)

    existing_ids = set()
    for fpath in files:
        with open(fpath, "r") as f:
            ema_links = json.loads(f.read())
        existing_ids.update(item['id'] for item in ema_links)

    print("Number of existing items = %d" % len(existing_ids))
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

def ema_print_domain_content(content, content_kind, courses, fname):
    """Export content within a given domain, passed in 'content' parameter,
    Only export content that is within whitelisted courses"""
    ema_content = []
    existing_ids = read_existing_links()
    unique_content_ids = existing_ids

    for v in content:

        course = v['course']
        # Only print content from a selected list of courses
        if course not in courses:
            continue

        subject = COURSE_SUBJECT_MAP[course]

        # Suuper ugly hack, this content is both in math and science domain
        # We already link it in physics course so we need to skip it in math.
        if v['node_slug'] in (
                'v/introduction-to-vectors-and-scalars', 'a/scientific-notation-review'
                ) and v['domain'] == 'math':
            unique_content_ids.add(v['id'])

        if v['node_slug'] in EXCLUDED_PROGRAMING_TOPICS:
            unique_content_ids.add(v['id'])
            continue

        if v['id'] in unique_content_ids:
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
            'typ': EMA_OPTIONAL_DATA['typ'][content_kind],
            'stupen_vzdelavani': EMA_OPTIONAL_DATA['stupen_vzdelavani'][course],
            'vzdelavaci_obor': EMA_OPTIONAL_DATA['vzdelavaci_obor'][subject],
            'gramotnost': EMA_OPTIONAL_DATA['gramotnost'][subject],
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

    print('Number of exported EMA %ss = %d' % (content_kind, len(ema_content)))


if __name__ == '__main__':

    opts = read_cmd()
    domain = opts.domain
    content_kind = opts.content.lower()

    if content_kind not in CONTENT_KINDS:
        print("ERROR: invalid content types: ", opts.content)
        print("Available content types: ", CONTENT_KINDS)
        exit(1)

    math_courses = set([
        'early-math', 'arithmetic', 'basic-geo', 
        'trigonometry', 'algebra-basics', 'pre-algebra',
        'vyrazy', 'funkce', 'analyticka-geometrie', 'komplexni-cisla',
        'differential-calculus', 'integralni-pocet',
        'posloupnosti-a-rady', 'pravdepodobnost-a-kombinatorika'
    ])

    science_courses = set([
            'fyzika-mechanika', 'fyzika-elektrina-a-magnetismus',
            'fyzika-vlneni-a-zvuk', 'obecna-chemie', 'fyzikalni-chemie',
            'organic-chemistry', 'biology'
    ])

    computing_courses = set(['informatika-pocitace-a-internet', 'code-org'])

    # For programming courses, we link and the lesson/course level,
    # not individual content items
    if content_kind == 'topic':
        computing_courses = set(['computer-programming'])

    domain_courses_map = {
            "math": math_courses,
            "science": science_courses,
            "computing": computing_courses
    }

    tsv = TsvContentReader(TSV_CONTENT_FILE)
    if content_kind == "topic":
        content = []
        for topic_kind in ("course", "unit", "lesson"):
            content += tsv.get_content(topic_kind, domain)
    else:
        content = tsv.get_content(content_kind, domain)

    out_fname = 'ka_%s_%s.json' % (domain, content_kind)
    courses = domain_courses_map[domain]

    ema_print_domain_content(content, content_kind, courses, out_fname)
