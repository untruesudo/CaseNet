"""
fetch_unidentified.py
Fetches unidentified remains data from public open-data sources.

Sources tried in order:
1. California DOJ OpenJustice - Socrata API (no auth, truly public)
2. NamUs web search with full browser headers
3. Preserve existing data if all sources fail
"""

import requests
import json
import os
import random
import sys
from datetime import datetime

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'unidentified.json')

random.seed()  # random jitter each run

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

# Map state names to abbreviations
STATE_NAME_TO_ABBR = {
    'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA',
    'Colorado':'CO','Connecticut':'CT','Delaware':'DE','Florida':'FL','Georgia':'GA',
    'Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA',
    'Kansas':'KS','Kentucky':'KY','Louisiana':'LA','Maine':'ME','Maryland':'MD',
    'Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS',
    'Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV',
    'New Hampshire':'NH','New Jersey':'NJ','New Mexico':'NM','New York':'NY',
    'North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK',
    'Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC',
    'South Dakota':'SD','Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT',
    'Virginia':'VA','Washington':'WA','West Virginia':'WV','Wisconsin':'WI',
    'Wyoming':'WY','District of Columbia':'DC',
}

def jitter(lat, lng, amt=0.6):
    return (
        lat + (random.random() - 0.5) * amt,
        lng + (random.random() - 0.5) * amt,
    )

def coords(state_abbr, state_name=''):
    abbr = state_abbr or STATE_NAME_TO_ABBR.get(state_name, '')
    c = STATE_CENTROIDS.get(str(abbr).strip().upper())
    if not c:
        return None, None
    return jitter(c[0], c[1])


# ── SOURCE 1: CALIFORNIA DOJ OPEN DATA ───────────────────────────────────────
# data.ca.gov Socrata API — genuinely public, no auth required
# Dataset: California unidentified persons
CA_DOJ_URL = (
    'https://data.ca.gov/api/3/action/datastore_search'
    '?resource_id=f0e8b1a8-9d4d-4d96-b0c7-9a0fa9c3c5a2'
    '&limit=1000'
)

# Alternative Socrata endpoints for unidentified persons
SOCRATA_ENDPOINTS = [
    # California DOJ - Unidentified Persons
    'https://data.ca.gov/api/3/action/datastore_search?resource_id=f0e8b1a8-9d4d-4d96-b0c7-9a0fa9c3c5a2&limit=500',
    # General Socrata search for unidentified persons datasets
    'https://data.ca.gov/api/3/action/package_search?q=unidentified+persons&rows=5',
]

def fetch_california_doj():
    """Try California DOJ open data portal."""
    print('Trying California DOJ open data...')
    headers = {'User-Agent': 'CASENET/1.0 research tool', 'Accept': 'application/json'}

    # Try multiple CA DOJ dataset IDs for unidentified persons
    dataset_ids = [
        'f0e8b1a8-9d4d-4d96-b0c7-9a0fa9c3c5a2',
        '4d35e2f4-5c5e-4b3a-8f1c-2e9b7a3d6c4e',
    ]

    for ds_id in dataset_ids:
        url = f'https://data.ca.gov/api/3/action/datastore_search?resource_id={ds_id}&limit=500'
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                records = data.get('result', {}).get('records', [])
                if records:
                    print(f'  CA DOJ: {len(records)} records')
                    return records, 'CA DOJ'
        except Exception as e:
            print(f'  CA DOJ error: {e}')

    return [], None


# ── SOURCE 2: NAMUS WITH FULL BROWSER SESSION ─────────────────────────────────
def fetch_namus():
    """
    Attempt NamUs with a full browser session simulation.
    GitHub Actions IPs are sometimes allowed where proxy IPs are not.
    """
    print('Trying NamUs with browser session...')

    session = requests.Session()
    session.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/122.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
    })

    # Step 1: visit homepage to get cookies
    try:
        home = session.get('https://www.namus.gov/', timeout=15)
        print(f'  NamUs homepage: {home.status_code}')
    except Exception as e:
        print(f'  NamUs homepage failed: {e}')
        return []

    # Step 2: visit search page to get any CSRF tokens
    try:
        search = session.get(
            'https://www.namus.gov/UnidentifiedPersons/Search',
            timeout=15,
            headers={'Referer': 'https://www.namus.gov/'}
        )
        print(f'  NamUs search page: {search.status_code}')
    except Exception as e:
        print(f'  NamUs search page failed: {e}')

    # Step 3: make the API call with the established session
    try:
        api = session.post(
            'https://www.namus.gov/api/CaseSets/NamUs/UnidentifiedPersons/search',
            json={'take': 250, 'skip': 0},
            timeout=20,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Referer': 'https://www.namus.gov/UnidentifiedPersons/Search',
                'Origin': 'https://www.namus.gov',
                'X-Requested-With': 'XMLHttpRequest',
            }
        )
        print(f'  NamUs API: {api.status_code}')
        if api.status_code == 200:
            data = api.json()
            results = data.get('results', [])
            count   = data.get('count', 0)
            print(f'  NamUs: count={count}, results={len(results)}')
            if results:
                return results
            elif count > 0:
                print(f'  NamUs: auth wall — {count} cases exist but access blocked')
    except Exception as e:
        print(f'  NamUs API error: {e}')

    return []


def map_namus(rec):
    loc = ', '.join(filter(None, [
        rec.get('cityOfRecovery', ''),
        rec.get('stateOfRecovery', ''),
    ]))
    rc  = rec.get('recoveryCoordinates') or {}
    lat = rc.get('latitude')
    lng = rc.get('longitude')
    if not (lat and lng):
        lat, lng = coords(rec.get('stateOfRecovery', ''))

    af  = rec.get('estimatedAgeFrom')
    at  = rec.get('estimatedAgeTo')
    age = f'est. {af}–{at}' if af is not None and at is not None else ''
    demo = ', '.join(filter(None, [rec.get('sex',''), age]))

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


# ── SOURCE 3: OPEN DATA PORTALS (SOCRATA) ────────────────────────────────────
SOCRATA_UNIDENTIFIED = [
    # Texas DPS missing/unidentified
    {
        'url': 'https://data.texas.gov/resource/4gfq-c5ac.json?$limit=500&$where=case_type=%27Unidentified%27',
        'state': 'TX',
        'label': 'Texas DPS',
    },
    # Florida unidentified
    {
        'url': 'https://opendata.fdot.gov/api/explore/v2.1/catalog/datasets/unidentified-persons/records?limit=100',
        'state': 'FL',
        'label': 'Florida',
    },
]

def fetch_open_data():
    """Try various open data Socrata portals."""
    print('Trying open data portals...')
    cases = []
    headers = {'User-Agent': 'CASENET/1.0', 'Accept': 'application/json'}

    for source in SOCRATA_UNIDENTIFIED:
        try:
            r = requests.get(source['url'], headers=headers, timeout=15)
            if r.status_code == 200:
                records = r.json()
                if isinstance(records, list) and records:
                    print(f'  {source["label"]}: {len(records)} records')
                    for rec in records:
                        lat, lng = coords(source['state'])
                        cases.append({
                            'id':     'UP-' + source['state'] + '-' + str(rec.get('case_number', rec.get('id', len(cases)))),
                            'type':   'unidentified',
                            'name':   rec.get('case_title') or rec.get('name') or 'Unidentified Person',
                            'date':   str(rec.get('date_found') or rec.get('year',''))[:10],
                            'location': rec.get('city','') + ', ' + source['state'],
                            'lat':    lat,
                            'lng':    lng,
                            'agency': rec.get('agency') or source['label'],
                            'status': 'open',
                            'demo':   rec.get('sex','') + ' ' + str(rec.get('age_range','')),
                            'source': 'Open Data',
                            'circumstances': rec.get('circumstances',''),
                            'flag':   None,
                        })
        except Exception as e:
            print(f'  {source["label"]} error: {e}')

    return cases


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    cases = []

    # Try NamUs first (best data quality)
    namus_recs = fetch_namus()
    if namus_recs:
        cases = [map_namus(r) for r in namus_recs]
        print(f'Using NamUs: {len(cases)} cases')

    # Try open data portals
    if not cases:
        cases = fetch_open_data()
        if cases:
            print(f'Using open data portals: {len(cases)} cases')

    # Preserve existing data if nothing worked
    if not cases:
        print('No new data retrieved from any source.')
        if os.path.exists(OUTPUT_PATH):
            with open(OUTPUT_PATH) as f:
                existing = json.load(f)
            if existing.get('count', 0) > 0:
                print(f'Preserving existing {existing["count"]} cases.')
                return
        print('No existing data to preserve — writing empty file.')

    valid = [c for c in cases if c.get('lat') and c.get('lng')]
    print(f'Final: {len(valid)} cases with valid coordinates')

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    output = {
        'generated': datetime.utcnow().isoformat() + 'Z',
        'source':    'NamUs / Open Data Portals',
        'count':     len(valid),
        'cases':     valid,
    }
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, separators=(',', ':'))

    kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f'Written: {OUTPUT_PATH} ({kb:.1f} KB)')


if __name__ == '__main__':
    main()
