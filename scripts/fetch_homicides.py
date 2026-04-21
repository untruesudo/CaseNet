"""
fetch_homicides.py
Downloads the Washington Post homicide database and converts it to CASENET JSON format.

Source: Washington Post "Murder with Impunity" dataset
URL: https://github.com/washingtonpost/data-homicides
License: Open for research and journalism use
Coverage: ~52,000 homicides across 50 major US cities, 2007–2017
"""

import requests
import csv
import json
import os
import sys
from datetime import datetime
from io import StringIO

# ── SOURCE ────────────────────────────────────────────────────────────────────
WAPO_URL = (
    'https://raw.githubusercontent.com/washingtonpost/data-homicides'
    '/master/homicide-data.csv'
)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'homicides.json')

# ── FIELD MAPPING ─────────────────────────────────────────────────────────────
# WaPo columns: uid, reported_date, victim_last, victim_first, victim_race,
#               victim_age, victim_sex, city, state, lat, lon, disposition

DISPOSITION_MAP = {
    'Open/No arrest':        'unsolved',
    'Closed without arrest': 'unsolved',
    'Closed by arrest':      'closed',
}

def map_record(row):
    """Convert a WaPo homicide row to CASENET case schema."""
    # Only include unsolved/open cases
    disposition = row.get('disposition', '')
    status      = DISPOSITION_MAP.get(disposition, 'unsolved')
    if status == 'closed':
        return None  # skip solved cases

    uid   = row.get('uid', '').strip()
    first = row.get('victim_first', '').strip().title()
    last  = row.get('victim_last',  '').strip().title()
    name  = (first + ' ' + last).strip() or 'Unknown'

    city  = row.get('city',  '').strip()
    state = row.get('state', '').strip()
    loc   = ', '.join(filter(None, [city, state])) or 'Unknown'

    # WaPo date format: YYYYMMDD
    raw_date = row.get('reported_date', '')
    try:
        date = datetime.strptime(str(raw_date)[:8], '%Y%m%d').strftime('%Y-%m-%d')
    except Exception:
        date = ''

    try:
        lat = float(row.get('lat', '') or 0) or None
        lng = float(row.get('lon', '') or 0) or None
    except (ValueError, TypeError):
        lat = lng = None

    race = row.get('victim_race', '').strip()
    age  = row.get('victim_age',  '').strip()
    sex  = row.get('victim_sex',  '').strip()
    demo = ', '.join(filter(lambda x: x and x.lower() not in ('unknown',''), [sex, age, race]))

    return {
        'id':           'UH-WAPO-' + uid,
        'type':         'homicide',
        'name':         name,
        'date':         date,
        'location':     loc,
        'lat':          lat,
        'lng':          lng,
        'agency':       city + ' Police Department' if city else 'Unknown Agency',
        'status':       status,
        'demo':         demo,
        'source':       'WaPo',
        'circumstances': disposition,
        'flag':         None,
    }

def main():
    print('Fetching Washington Post homicide data...')
    try:
        r = requests.get(WAPO_URL, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f'ERROR: Could not fetch WaPo data: {e}')
        sys.exit(1)

    reader  = csv.DictReader(StringIO(r.text))
    cases   = []
    total   = 0
    skipped = 0

    for row in reader:
        total += 1
        case = map_record(row)
        if case:
            cases.append(case)
        else:
            skipped += 1

    print(f'Processed {total} records → {len(cases)} unsolved, {skipped} solved (skipped)')

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    output = {
        'generated':  datetime.utcnow().isoformat() + 'Z',
        'source':     'Washington Post — Murder with Impunity dataset',
        'source_url': 'https://github.com/washingtonpost/data-homicides',
        'license':    'Open for research and journalism use',
        'count':      len(cases),
        'cases':      cases,
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, separators=(',', ':'))

    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f'Written to {OUTPUT_PATH} ({size_kb:.1f} KB)')

if __name__ == '__main__':
    main()
