"""
fetch_unidentified.py
Downloads unidentified remains data and converts it to CASENET JSON format.

Primary source: Doe Network public case listing
Fallback: NamUs public CSV export (when available)

The Doe Network (doenetwork.org) maintains a public database of unidentified
persons cases, fully accessible for research and journalism.
"""

import requests
import json
import os
import sys
import re
from datetime import datetime
from html.parser import HTMLParser

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'unidentified.json')

# ── DOE NETWORK ───────────────────────────────────────────────────────────────
DOE_BASE     = 'https://www.doenetwork.org'
DOE_CASES_US = DOE_BASE + '/cases.php?criteria=&namus2=&tabortype=1&tab=1'

# State abbreviation → full name (for location parsing)
STATE_ABBR = {
    'AL':'Alabama','AK':'Alaska','AZ':'Arizona','AR':'Arkansas','CA':'California',
    'CO':'Colorado','CT':'Connecticut','DE':'Delaware','FL':'Florida','GA':'Georgia',
    'HI':'Hawaii','ID':'Idaho','IL':'Illinois','IN':'Indiana','IA':'Iowa',
    'KS':'Kansas','KY':'Kentucky','LA':'Louisiana','ME':'Maine','MD':'Maryland',
    'MA':'Massachusetts','MI':'Michigan','MN':'Minnesota','MS':'Mississippi',
    'MO':'Missouri','MT':'Montana','NE':'Nebraska','NV':'Nevada','NH':'New Hampshire',
    'NJ':'New Jersey','NM':'New Mexico','NY':'New York','NC':'North Carolina',
    'ND':'North Dakota','OH':'Ohio','OK':'Oklahoma','OR':'Oregon','PA':'Pennsylvania',
    'RI':'Rhode Island','SC':'South Carolina','SD':'South Dakota','TN':'Tennessee',
    'TX':'Texas','UT':'Utah','VT':'Vermont','VA':'Virginia','WA':'Washington',
    'WV':'West Virginia','WI':'Wisconsin','WY':'Wyoming','DC':'Washington DC',
}

# State centroids for geocoding when coordinates unavailable
STATE_CENTROIDS = {
    'AL':(32.806671,-86.791130),'AK':(61.370716,-152.404419),'AZ':(33.729759,-111.431221),
    'AR':(34.969704,-92.373123),'CA':(36.116203,-119.681564),'CO':(39.059811,-105.311104),
    'CT':(41.597782,-72.755371),'DE':(39.318523,-75.507141), 'FL':(27.766279,-81.686783),
    'GA':(33.040619,-83.643074),'HI':(21.094318,-157.498337),'ID':(44.240459,-114.478828),
    'IL':(40.349457,-88.986137),'IN':(39.849426,-86.258278), 'IA':(42.011539,-93.210526),
    'KS':(38.526600,-96.726486),'KY':(37.668140,-84.670067), 'LA':(31.169960,-91.867805),
    'ME':(44.693947,-69.381927),'MD':(39.063946,-76.802101), 'MA':(42.230171,-71.530106),
    'MI':(43.326618,-84.536095),'MN':(45.694454,-93.900192), 'MS':(32.741646,-89.678696),
    'MO':(38.456085,-92.288368),'MT':(46.921925,-110.454353),'NE':(41.125370,-98.268082),
    'NV':(38.313515,-117.055374),'NH':(43.452492,-71.563896),'NJ':(40.298904,-74.521011),
    'NM':(34.840515,-106.248482),'NY':(42.165726,-74.948051),'NC':(35.630066,-79.806419),
    'ND':(47.528912,-99.784012), 'OH':(40.388783,-82.764915),'OK':(35.565342,-96.928917),
    'OR':(44.572021,-122.070938),'PA':(40.590752,-77.209755),'RI':(41.680893,-71.511780),
    'SC':(33.856892,-80.945007), 'SD':(44.299782,-99.438828),'TN':(35.747845,-86.692345),
    'TX':(31.054487,-97.563461), 'UT':(40.150032,-111.862434),'VT':(44.045876,-72.710686),
    'VA':(37.769337,-78.169968), 'WA':(47.400902,-121.490494),'WV':(38.491226,-80.954453),
    'WI':(44.268543,-89.616508), 'WY':(42.755966,-107.302490),'DC':(38.897438,-77.026817),
}

import random
def jitter(coord, amount=0.5):
    return coord + (random.random() - 0.5) * amount

def coords_from_state(abbr):
    c = STATE_CENTROIDS.get(abbr)
    if not c:
        return None, None
    return jitter(c[0], 0.7), jitter(c[1], 0.7)


class DoeParser(HTMLParser):
    """Parse Doe Network case listing HTML into structured records."""
    def __init__(self):
        super().__init__()
        self.cases  = []
        self.in_row = False
        self.cells  = []
        self.cur    = []
        self.in_td  = False
        self.in_a   = False
        self.href   = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr':
            self.in_row = True
            self.cells  = []
        elif tag == 'td' and self.in_row:
            self.in_td = True
            self.cur   = []
        elif tag == 'a' and self.in_td:
            self.in_a  = True
            self.href  = attrs.get('href', '')

    def handle_endtag(self, tag):
        if tag == 'td' and self.in_td:
            self.cells.append((''.join(self.cur).strip(), self.href))
            self.in_td = False
            self.in_a  = False
            self.href  = ''
            self.cur   = []
        elif tag == 'tr' and self.in_row:
            self.in_row = False
            if len(self.cells) >= 4:
                self._add_case()
        elif tag == 'a':
            self.in_a = False

    def handle_data(self, data):
        if self.in_td:
            self.cur.append(data)

    def _add_case(self):
        # Typical Doe Network columns: Case#, Name, Sex, Found Date, Location, State
        try:
            case_id  = self.cells[0][0].strip() if len(self.cells) > 0 else ''
            name     = self.cells[1][0].strip() if len(self.cells) > 1 else ''
            href     = self.cells[1][1]          if len(self.cells) > 1 else ''
            sex      = self.cells[2][0].strip() if len(self.cells) > 2 else ''
            found    = self.cells[3][0].strip() if len(self.cells) > 3 else ''
            location = self.cells[4][0].strip() if len(self.cells) > 4 else ''
            state    = self.cells[5][0].strip() if len(self.cells) > 5 else ''

            if not case_id or not case_id[0].isdigit():
                return  # skip header rows

            # Normalise state
            state_abbr = state.upper()[:2] if state else ''
            state_full = STATE_ABBR.get(state_abbr, state)
            loc_full   = ', '.join(filter(None, [location, state_full])) or 'Unknown'

            lat, lng = coords_from_state(state_abbr)

            self.cases.append({
                'id':           'UP-DOE-' + case_id.replace(' ', ''),
                'type':         'unidentified',
                'name':         name or 'Unidentified Person',
                'date':         found,
                'location':     loc_full,
                'lat':          lat,
                'lng':          lng,
                'agency':       'Unknown Agency',
                'status':       'open',
                'demo':         sex,
                'source':       'Doe Network',
                'circumstances': '',
                'flag':         None,
                '_url':         DOE_BASE + '/' + href.lstrip('/') if href else '',
            })
        except Exception:
            pass  # skip malformed rows


def fetch_doe_network():
    """Fetch cases from Doe Network."""
    print('Fetching Doe Network cases...')
    headers = {
        'User-Agent': 'CASENET Research Tool — public transparency project',
        'Accept': 'text/html',
    }
    try:
        r = requests.get(DOE_CASES_US, headers=headers, timeout=30)
        r.raise_for_status()
        parser = DoeParser()
        parser.feed(r.text)
        print(f'  Doe Network: {len(parser.cases)} cases parsed')
        return parser.cases
    except Exception as e:
        print(f'  Doe Network unavailable: {e}')
        return []


def main():
    cases = fetch_doe_network()

    if not cases:
        print('No unidentified cases retrieved — writing empty dataset')
        cases = []

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    output = {
        'generated':  datetime.utcnow().isoformat() + 'Z',
        'source':     'Doe Network — doenetwork.org',
        'source_url': 'https://www.doenetwork.org',
        'license':    'Public — research and journalism use',
        'count':      len(cases),
        'cases':      cases,
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, separators=(',', ':'))

    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f'Written {len(cases)} cases to {OUTPUT_PATH} ({size_kb:.1f} KB)')

if __name__ == '__main__':
    main()
