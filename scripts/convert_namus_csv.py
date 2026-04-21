"""
convert_namus_csv.py
Converts a manually downloaded NamUs CSV export to CASENET JSON format.

HOW TO GET THE CSV:
1. Go to https://www.namus.gov/UnidentifiedPersons/Search
2. Leave all filters blank and click Search
3. Click "Export Results" or "Download CSV" (bottom of results)
4. Save the file as: data/namus_unidentified_raw.csv

Then run:
    python3 scripts/convert_namus_csv.py

This generates data/unidentified.json ready for the site.
"""

import csv
import json
import os
import sys
import random
from datetime import datetime

INPUT_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'namus_unidentified_raw.csv')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'unidentified.json')

random.seed()

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

def coords(state_raw):
    # Try as abbreviation first, then as full name
    abbr = str(state_raw).strip().upper()[:2]
    if abbr in STATE_CENTROIDS:
        return jitter(*STATE_CENTROIDS[abbr])
    full = str(state_raw).strip().title()
    abbr2 = STATE_NAME_TO_ABBR.get(full, '')
    if abbr2 in STATE_CENTROIDS:
        return jitter(*STATE_CENTROIDS[abbr2])
    return None, None

def find_col(headers, *candidates):
    """Find the first matching column name (case-insensitive)."""
    h_lower = {h.lower().strip(): h for h in headers}
    for c in candidates:
        if c.lower() in h_lower:
            return h_lower[c.lower()]
    return None

def convert(input_path):
    if not os.path.exists(input_path):
        print(f'ERROR: Input file not found: {input_path}')
        print()
        print('Please download the NamUs CSV:')
        print('  1. Go to https://www.namus.gov/UnidentifiedPersons/Search')
        print('  2. Search with no filters')
        print('  3. Click "Export Results" / "Download CSV"')
        print('  4. Save as: data/namus_unidentified_raw.csv')
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.DictReader(f)
        rows   = list(reader)
        headers = reader.fieldnames or []

    print(f'Loaded {len(rows)} rows from {input_path}')
    print(f'Columns: {headers[:10]}...')

    # Auto-detect column names — NamUs CSV headers vary by export version
    col_id      = find_col(headers, 'Case Number', 'CaseNumber', 'NamUs #', 'NamUsNumber', 'ID')
    col_title   = find_col(headers, 'Case Title', 'CaseTitle', 'Title', 'Name')
    col_date    = find_col(headers, 'Date Found', 'DateFound', 'Recovery Date', 'RecoveryDate')
    col_city    = find_col(headers, 'City of Recovery', 'CityOfRecovery', 'City')
    col_state   = find_col(headers, 'State of Recovery', 'StateOfRecovery', 'State')
    col_agency  = find_col(headers, 'Agency Name', 'AgencyName', 'Agency')
    col_sex     = find_col(headers, 'Sex', 'Gender')
    col_age_min = find_col(headers, 'Estimated Age From', 'EstimatedAgeFrom', 'Age From', 'Min Age')
    col_age_max = find_col(headers, 'Estimated Age To', 'EstimatedAgeTo', 'Age To', 'Max Age')
    col_circ    = find_col(headers, 'Circumstances of Recovery', 'Circumstances', 'Description')
    col_lat     = find_col(headers, 'Latitude', 'Lat')
    col_lng     = find_col(headers, 'Longitude', 'Lon', 'Lng')

    print(f'Detected columns: id={col_id}, title={col_title}, date={col_date}, state={col_state}')

    cases = []
    for row in rows:
        case_num = str(row.get(col_id, '') if col_id else '').strip()
        title    = str(row.get(col_title, '') if col_title else '').strip()
        date     = str(row.get(col_date, '') if col_date else '').strip()[:10]
        city     = str(row.get(col_city, '') if col_city else '').strip()
        state    = str(row.get(col_state, '') if col_state else '').strip()
        agency   = str(row.get(col_agency, '') if col_agency else '').strip()
        sex      = str(row.get(col_sex, '') if col_sex else '').strip()
        age_min  = str(row.get(col_age_min, '') if col_age_min else '').strip()
        age_max  = str(row.get(col_age_max, '') if col_age_max else '').strip()
        circ     = str(row.get(col_circ, '') if col_circ else '').strip()

        # Coordinates — use from CSV if available, otherwise centroid
        lat_raw = row.get(col_lat, '') if col_lat else ''
        lng_raw = row.get(col_lng, '') if col_lng else ''
        try:
            lat = float(lat_raw) if lat_raw else None
            lng = float(lng_raw) if lng_raw else None
        except ValueError:
            lat = lng = None

        if not lat or not lng:
            lat, lng = coords(state)

        if not lat or not lng:
            continue  # skip if no location at all

        age_str = ''
        if age_min and age_max:
            age_str = f'est. {age_min}–{age_max}'
        elif age_min:
            age_str = f'est. {age_min}+'
        demo = ', '.join(filter(None, [sex, age_str]))
        loc  = ', '.join(filter(None, [city, state]))

        cases.append({
            'id':           'UP-' + (case_num or str(len(cases))),
            'type':         'unidentified',
            'name':         title or 'Unidentified Person',
            'date':         date,
            'location':     loc or 'Unknown',
            'lat':          lat,
            'lng':          lng,
            'agency':       agency or 'Unknown Agency',
            'status':       'open',
            'demo':         demo,
            'source':       'NamUs',
            'circumstances': circ,
            'flag':         None,
        })

    return cases

def main():
    cases = convert(INPUT_PATH)
    print(f'Converted {len(cases)} cases with valid coordinates')

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    output = {
        'generated': datetime.utcnow().isoformat() + 'Z',
        'source':    'NamUs — manually exported CSV',
        'count':     len(cases),
        'cases':     cases,
    }
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, separators=(',', ':'))

    kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f'Written: {OUTPUT_PATH} ({kb:.1f} KB, {len(cases)} cases)')
    print()
    print('Next step: commit data/unidentified.json to your GitHub repo.')

if __name__ == '__main__':
    main()
