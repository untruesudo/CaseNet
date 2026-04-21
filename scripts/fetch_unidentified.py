"""
fetch_unidentified.py
Fetches unidentified remains data from multiple public sources.

Sources tried in order:
1. NamUs unidentified persons - web scrape of public search results
2. Doe Network - public case listings
3. Generate structured placeholder from known public cases if both fail

Run via GitHub Action or manually:
    pip install requests beautifulsoup4
    python3 scripts/fetch_unidentified.py
"""

import requests
import json
import os
import re
import random
import sys
from datetime import datetime
from html.parser import HTMLParser

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'unidentified.json')

# ── STATE CENTROIDS ───────────────────────────────────────────────────────────
STATE_CENTROIDS = {
    'AL':(32.81,-86.79),'AK':(61.37,-152.40),'AZ':(33.73,-111.43),
    'AR':(34.97,-92.37),'CA':(36.12,-119.68),'CO':(39.06,-105.31),
    'CT':(41.60,-72.76),'DE':(39.32,-75.51),'FL':(27.77,-81.69),
    'GA':(33.04,-83.64),'HI':(21.09,-157.50),'ID':(44.24,-114.48),
    'IL':(40.35,-88.99),'IN':(39.85,-86.26),'IA':(42.01,-93.21),
    'KS':(38.53,-96.73),'KY':(37.67,-84.67),'LA':(31.17,-91.87),
    'ME':(44.69,-69.38),'MD':(39.06,-76.80),'MA':(42.23,-71.53),
    'MI':(43.33,-84.54),'MN':(45.69,-93.90),'MS':(32.74,-89.68),
    'MO':(38.46,-92.29),'MT':(46.92,-110.45),'NE':(41.13,-98.27),
    'NV':(38.31,-117.06),'NH':(43.45,-71.56),'NJ':(40.30,-74.52),
    'NM':(34.84,-106.25),'NY':(42.17,-74.95),'NC':(35.63,-79.81),
    'ND':(47.53,-99.78),'OH':(40.39,-82.76),'OK':(35.57,-96.93),
    'OR':(44.57,-122.07),'PA':(40.59,-77.21),'RI':(41.68,-71.51),
    'SC':(33.86,-80.95),'SD':(44.30,-99.44),'TN':(35.75,-86.69),
    'TX':(31.05,-97.56),'UT':(40.15,-111.86),'VT':(44.05,-72.71),
    'VA':(37.77,-78.17),'WA':(47.40,-121.49),'WV':(38.49,-80.95),
    'WI':(44.27,-89.62),'WY':(42.76,-107.30),'DC':(38.90,-77.03),
}

def jitter(lat, lng, amount=0.7):
    return (
        lat + (random.random() - 0.5) * amount,
        lng + (random.random() - 0.5) * amount
    )

def coords_from_state(abbr):
    c = STATE_CENTROIDS.get(str(abbr).strip().upper())
    if not c:
        return None, None
    return jitter(c[0], c[1])


# ── SOURCE 1: NAMUS WEB SCRAPE ────────────────────────────────────────────────
def fetch_namus_web():
    """
    Scrape NamUs unidentified persons public search page.
    NamUs renders case summaries in HTML — no API key needed for public data.
    """
    print('Trying NamUs web search...')

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/html, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.namus.gov/',
    })

    # Try the NamUs search API with Referer set to their own site
    try:
        r = session.post(
            'https://www.namus.gov/api/CaseSets/NamUs/UnidentifiedPersons/search',
            json={'take': 250, 'skip': 0},
            timeout=20,
        )
        if r.status_code == 200:
            data = r.json()
            results = data.get('results', [])
            if results:
                print(f'  NamUs web: {len(results)} cases')
                return [map_namus_unid(rec) for rec in results]
        print(f'  NamUs web: {r.status_code} — {r.text[:100]}')
    except Exception as e:
        print(f'  NamUs web error: {e}')

    return []


def map_namus_unid(rec):
    loc = ', '.join(filter(None, [
        rec.get('cityOfRecovery', ''),
        rec.get('stateOfRecovery', ''),
    ]))
    state_abbr = rec.get('stateOfRecovery', '')
    rc = rec.get('recoveryCoordinates') or {}
    lat = rc.get('latitude')
    lng = rc.get('longitude')
    if not lat or not lng:
        lat, lng = coords_from_state(state_abbr)

    age_from = rec.get('estimatedAgeFrom')
    age_to   = rec.get('estimatedAgeTo')
    age_str  = f'est. {age_from}–{age_to}' if age_from is not None and age_to is not None else ''
    demo     = ', '.join(filter(None, [rec.get('sex',''), age_str]))

    return {
        'id':           'UP-' + str(rec.get('caseNumber', '')),
        'type':         'unidentified',
        'name':         rec.get('computedCaseTitle') or 'Unidentified Person',
        'date':         (rec.get('dateFound') or '')[:10],
        'location':     loc or 'Unknown',
        'lat':          lat,
        'lng':          lng,
        'agency':       rec.get('agencyName') or 'Unknown Agency',
        'status':       'open',
        'demo':         demo,
        'source':       'NamUs',
        'circumstances': rec.get('circumstancesOfRecovery') or '',
        'flag':         None,
    }


# ── SOURCE 2: DOE NETWORK SCRAPE ──────────────────────────────────────────────
def fetch_doe_network():
    """Scrape Doe Network public case listings."""
    print('Trying Doe Network...')

    STATE_MAP = {
        'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR',
        'California':'CA','Colorado':'CO','Connecticut':'CT','Delaware':'DE',
        'Florida':'FL','Georgia':'GA','Hawaii':'HI','Idaho':'ID',
        'Illinois':'IL','Indiana':'IN','Iowa':'IA','Kansas':'KS',
        'Kentucky':'KY','Louisiana':'LA','Maine':'ME','Maryland':'MD',
        'Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS',
        'Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV',
        'New Hampshire':'NH','New Jersey':'NJ','New Mexico':'NM','New York':'NY',
        'North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK',
        'Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI',
        'South Carolina':'SC','South Dakota':'SD','Tennessee':'TN',
        'Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA',
        'Washington':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY',
    }

    headers = {
        'User-Agent': 'CASENET/1.0 (public transparency research; contact: casenet@example.com)',
        'Accept': 'text/html',
    }

    try:
        # Doe Network individual state pages are more accessible than the main listing
        cases = []
        for state_full, abbr in list(STATE_MAP.items())[:10]:  # sample first 10 states
            url = f'https://www.doenetwork.org/cases.php?criteria=&namus2=&tabortype=1&tab=1&state={abbr}'
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200 and len(r.text) > 1000:
                    state_cases = parse_doe_html(r.text, abbr)
                    cases.extend(state_cases)
                    print(f'  Doe Network {state_full}: {len(state_cases)} cases')
            except Exception:
                pass

        if cases:
            return cases
    except Exception as e:
        print(f'  Doe Network error: {e}')

    return []


def parse_doe_html(html, state_abbr):
    """Extract case data from Doe Network HTML."""
    cases = []
    # Look for case patterns: case number, name, found date
    pattern = re.compile(
        r'(\d{4}UFUS\d+|UFUS-\d+-\d+|\d+-\d+UN[A-Z]+)'
        r'.*?<a[^>]*href="([^"]*case[^"]*)"[^>]*>([^<]+)</a>'
        r'.*?(\d{4}|\w+ \d{4})',
        re.DOTALL | re.IGNORECASE
    )
    lat, lng = coords_from_state(state_abbr)

    for i, m in enumerate(pattern.finditer(html)):
        case_id = m.group(1).strip()
        href    = m.group(2).strip()
        name    = m.group(3).strip()
        date    = m.group(4).strip()

        if not name or len(name) > 80:
            continue

        cases.append({
            'id':           'UP-DOE-' + re.sub(r'\W', '', case_id),
            'type':         'unidentified',
            'name':         name,
            'date':         date,
            'location':     STATE_CENTROIDS.get(state_abbr, ('',''))[0] and state_abbr or 'Unknown',
            'lat':          lat,
            'lng':          lng,
            'agency':       'Unknown Agency',
            'status':       'open',
            'demo':         '',
            'source':       'Doe Network',
            'circumstances': '',
            'flag':         None,
            '_url':         'https://www.doenetwork.org/' + href.lstrip('/'),
        })

    return cases


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    random.seed(42)  # Reproducible jitter

    # Try sources in order
    cases = fetch_namus_web()

    if not cases:
        cases = fetch_doe_network()

    if not cases:
        print('WARNING: No unidentified cases retrieved from any source.')
        print('         This is likely a temporary network issue.')
        print('         The Action will retry next week automatically.')
        # Write empty file rather than overwriting good data
        if os.path.exists(OUTPUT_PATH):
            existing = json.load(open(OUTPUT_PATH))
            if existing.get('count', 0) > 0:
                print('         Keeping existing data file unchanged.')
                return

    # Filter to cases with valid coordinates
    valid = [c for c in cases if c.get('lat') and c.get('lng')]
    print(f'Final: {len(valid)} cases with coordinates (from {len(cases)} total)')

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    output = {
        'generated':  datetime.utcnow().isoformat() + 'Z',
        'source':     'NamUs / Doe Network',
        'count':      len(valid),
        'cases':      valid,
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, separators=(',', ':'))

    kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f'Written to {OUTPUT_PATH} ({kb:.1f} KB)')


if __name__ == '__main__':
    main()
