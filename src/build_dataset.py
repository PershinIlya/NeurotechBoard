#!/usr/bin/env python3
"""
Build neurotech dataset from scraped reccy.dev data.
Parses raw_dump.txt (pipe-delimited), enriches with founding years from knowledge,
derives country, primary sector, modality, invasiveness, and writes a CSV.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw' / 'reccy_dump_2026-04-09.txt'
OUT_CSV = ROOT / 'data' / 'processed' / 'neurotech_enriched.csv'

# -------- Founding year knowledge base --------
# Key: lowercased canonical-ish name token. Values from training knowledge + well-known sources.
# "confidence": H = well-known public info, M = reasonable estimate, L = rough guess.
FOUNDING = {
    # Public companies & very well-known
    'neuralink': (2016, 'H'),
    'synchron': (2016, 'H'),
    'paradromics': (2015, 'H'),
    'blackrock neurotech': (2008, 'H'),
    'precision neuroscience': (2021, 'H'),
    'science corp': (2021, 'H'),
    'kernel': (2016, 'H'),
    'motif neurotech': (2021, 'H'),
    'subsense': (2022, 'M'),
    'inner cosmos': (2020, 'M'),
    'neuropace': (1997, 'H'),
    'medtronic': (1949, 'H'),
    'boston scientific corporation': (1979, 'H'),
    'livanova plc': (2015, 'H'),
    'natus medical incorporated': (1987, 'H'),
    'essilorluxottica': (2018, 'H'),
    'meta platforms, inc.': (2004, 'H'),
    'bioventus': (2012, 'H'),
    'hinge health, inc.': (2014, 'H'),
    'oura': (2013, 'H'),
    'eight sleep': (2014, 'H'),
    'lumosity': (2005, 'H'),
    'brainsway': (2003, 'H'),
    'insightec ltd.': (1999, 'H'),
    'brainchip': (2011, 'H'),
    'hyperfine, inc. and the swoop® portable mr imaging® system': (2014, 'H'),
    'onward medical n.v.': (2014, 'H'),
    'nexstim': (2000, 'H'),
    'saluda medical': (2006, 'H'),
    'inspire medical systems': (2007, 'H'),
    'alto neuroscience inc': (2019, 'H'),
    'ceribell': (2014, 'H'),
    'cefaly technology': (2009, 'H'),
    'electrocore': (2005, 'H'),
    'pixium vision': (2012, 'H'),
    'magstim': (1985, 'H'),
    'neurostar': (2003, 'M'),  # Neuronetics
    'bluewind medical': (2010, 'M'),
    'presidio medical': (2017, 'M'),
    'cala health inc.': (2014, 'H'),
    'xrhealth': (2016, 'M'),
    'salvia bioelectronics b.v.': (2017, 'M'),
    'empatica': (2011, 'H'),
    'muse by interaxon': (2007, 'H'),
    'emotiv': (2011, 'H'),
    'neurosky': (2004, 'H'),
    'openbci': (2014, 'H'),
    'neurable': (2015, 'H'),
    'brainco': (2015, 'H'),
    'mindmaze therapeutics': (2012, 'M'),
    'nextsense': (2021, 'M'),
    'nerivio': (2014, 'M'),  # Theranica
    'cognito therapeutics': (2016, 'H'),
    'neurolutions': (2007, 'M'),
    'bitbrain': (2010, 'M'),
    'neuroelectrics': (2011, 'H'),
    'inbrain-neuroelectronics': (2019, 'M'),
    'starlab': (2000, 'M'),
    'beacon biosignals': (2019, 'H'),
    'rune labs': (2018, 'M'),
    'dreem': (2014, 'H'),
    'mendi.io': (2018, 'M'),
    'neurovalens': (2012, 'M'),
    'flow neuroscience': (2016, 'H'),
    'neurosity': (2019, 'H'),
    'neurotrack cognitive function test': (2012, 'M'),
    'neurolief': (2015, 'M'),
    'brainomix limited': (2010, 'M'),
    'icometrix': (2011, 'M'),
    'fisher wallace laboratories, inc.': (2007, 'M'),
    'neuromod devices ltd.': (2010, 'M'),
    'xsensio': (2014, 'M'),
    'phagenesis limited': (2007, 'M'),
    'neurovirt': (2018, 'L'),
    'aleva neuro': (2008, 'M'),
    'g.tec neurotechnology gmbh': (1999, 'H'),
    'ant neuro': (2000, 'M'),
    '3brain ag': (2011, 'M'),
    'magstim': (1985, 'H'),
    'cirtecmed': (1993, 'M'),
    'route 92 medical': (2014, 'M'),
    'darmiyan': (2015, 'M'),
    'spark biomedical inc': (2018, 'M'),
    'envoy medical, inc.': (2000, 'M'),
    'neuraxis': (2014, 'M'),
    'mainstay medical': (2008, 'M'),
    'nalu medical': (2013, 'M'),
    'spr therapeutics': (2011, 'M'),
    'curonix': (2023, 'M'),  # formerly Stimwave rebrand
    'uromems sas': (2011, 'M'),
    'terumo neuro': (2023, 'M'),  # formerly MicroVention/Terumo neuro
    'clearpoint neuro': (1998, 'M'),
    'ant neuro': (2000, 'M'),
    'neuspera medical': (2014, 'M'),
    'brain.q technologies inc.': (2015, 'M'),
    'neurolight': (2021, 'L'),
    'axoft': (2019, 'H'),
    'iota biosciences, inc.': (2017, 'H'),
    'phantom neuro': (2020, 'M'),
    'elemind': (2021, 'M'),
    'afference': (2020, 'M'),
    'nia therapeutics, inc.': (2018, 'M'),
    'firefly neuroscience, inc.': (2013, 'M'),
    'comind': (2018, 'M'),
    'beacon biosignals': (2019, 'H'),
    'brainify.ai': (2021, 'L'),
    'neurosoft-bio': (2020, 'L'),
    'neuraura biotech inc': (2018, 'L'),
    'alljoined': (2023, 'L'),
    'merge labs': (2025, 'M'),
    'nocira': (2014, 'M'),
    'nubrain- thoughts to text, image and speech decoding': (2022, 'L'),
    'cionic': (2018, 'M'),
    'cortec-neuro': (2010, 'M'),
    'neurons medical': (2008, 'M'),
    'stimdia': (2014, 'L'),
    'neurosteer': (2012, 'M'),
    'lifescapes': (2019, 'L'),
    'looxid labs': (2015, 'M'),
    'bios': (2015, 'M'),
    'medrhythms, inc.': (2016, 'M'),
    'noctrix health': (2018, 'M'),
    'fasikl': (2018, 'L'),
    'myndspan': (2019, 'L'),
    'psyonic': (2015, 'M'),
    'epiminder': (2016, 'M'),
    'vistim labs inc.': (2020, 'L'),
    'bia neuroscience': (2019, 'L'),
    'theta neurotech': (2022, 'L'),
    'brill neurotech': (2022, 'L'),
    'constellation': (2023, 'L'),
    'synaptrix-labs': (2022, 'L'),
    'xpanceo': (2021, 'M'),
    'frenz™ by earable™ neuroscience': (2018, 'M'),
    'naox': (2019, 'L'),
    'samphire neuroscience': (2021, 'L'),
    'newronika': (2008, 'M'),
    'wisear': (2019, 'L'),
    'idun technologies': (2017, 'M'),
    'epitel': (2014, 'L'),
    'epiwatch®': (2018, 'L'),
    'pulsetto': (2021, 'L'),
    'bottneuro ag': (2019, 'L'),
    'sens.ai': (2017, 'L'),
    'ampa': (2022, 'L'),
    'omniscient neurotechnology': (2018, 'M'),
    'galvanize': (2015, 'M'),
    'brain4': (2013, 'L'),
    'cognixion®': (2014, 'M'),
    'neurophet': (2016, 'L'),
    'ŌURA': (2013, 'H'),  # duplicate guard
    'positrigo': (2018, 'M'),
    'machinemd': (2019, 'L'),
    'iconeus': (2011, 'M'),
    'digilens': (2003, 'M'),
    'neuraled': (2017, 'L'),
    'neuralight': (2021, 'L'),
    'eneura': (2008, 'M'),
    'sinapticatx': (2019, 'L'),
    'wave neuroscience': (2014, 'L'),
    'lumithera': (2013, 'M'),
    'nyxoah': (2009, 'M'),
    'bioserenity': (2013, 'M'),
    'galvani bioelectronics': (2016, 'H'),
    'vielight': (2010, 'L'),
    'hyperfine': (2014, 'H'),
    'smartlens inc': (2020, 'L'),
    'huMannity medtec': (2020, 'L'),
    'canaery': (2020, 'L'),
    'coherence': (2021, 'L'),
    'sanmai technologies': (2020, 'L'),
    'axion': (2020, 'L'),
    'tiposi': (2022, 'L'),
    'surf therapeutics': (2019, 'L'),
    'attune neurosciences': (2020, 'L'),
    'secondwave systems': (2017, 'L'),
    'enterra medical, inc.': (2017, 'M'),  # spun out
    'mad science group inc.': (1985, 'M'),
    'cadenceneuro': (2018, 'L'),
    'valencia technologies': (2011, 'M'),
    'glneurotech': (1994, 'L'),
    'great lakes neurotechnologies': (1994, 'L'),
    'highland instruments highland instruments': (2007, 'L'),
    'histosonics': (2009, 'M'),
    'bexorg, inc.': (2019, 'L'),
    'pigpug health': (2019, 'L'),
    'mobia': (2015, 'L'),
    'emtel': (2018, 'L'),
    'cionic': (2018, 'M'),
    'steadiwear inc.': (2015, 'L'),
    'axoneurotech.com': (2020, 'L'),
    'syntropic medical': (2020, 'L'),
    'connectome': (2020, 'L'),
    'zeto-inc': (2015, 'L'),
    'imotions': (2005, 'M'),
    'i motions': (2005, 'M'),
    'magnetic tides': (2023, 'L'),
    'lunapharma': (2018, 'L'),
    'lungpacer': (2009, 'M'),
    'senseneuro': (2021, 'L'),
    'reccy': (2024, 'M'),
}

# -------- Country derivation --------
COUNTRY_MAP = {
    'CA': 'USA', 'NY': 'USA', 'MA': 'USA', 'TX': 'USA', 'FL': 'USA', 'IL': 'USA',
    'WA': 'USA', 'OR': 'USA', 'CO': 'USA', 'AZ': 'USA', 'UT': 'USA', 'OH': 'USA',
    'MI': 'USA', 'MN': 'USA', 'WI': 'USA', 'IN': 'USA', 'NJ': 'USA', 'CT': 'USA',
    'VA': 'USA', 'NC': 'USA', 'GA': 'USA', 'PA': 'USA', 'MD': 'USA', 'NV': 'USA',
    'KY': 'USA', 'MO': 'USA', 'TN': 'USA', 'LA': 'USA', 'AL': 'USA', 'SC': 'USA',
    'DE': 'USA', 'VT': 'USA',
    'California': 'USA', 'New York': 'USA', 'Massachusetts': 'USA',
    'Washington': 'USA', 'Texas': 'USA', 'Missouri': 'USA', 'Minnesota': 'USA',
    'Pennsylvania': 'USA', 'Maryland': 'USA', 'Illinois': 'USA',
    'United States': 'USA', 'USA': 'USA', 'US': 'USA',
    'UK': 'UK', 'United Kingdom': 'UK', 'England': 'UK',
    'France': 'France', 'Germany': 'Germany', 'Italy': 'Italy', 'Spain': 'Spain',
    'Switzerland': 'Switzerland', 'Netherlands': 'Netherlands',
    'The Netherlands': 'Netherlands',
    'Belgium': 'Belgium', 'Ireland': 'Ireland', 'Sweden': 'Sweden',
    'Denmark': 'Denmark', 'Norway': 'Norway', 'Finland': 'Finland',
    'Austria': 'Austria', 'Lithuania': 'Lithuania', 'Poland': 'Poland',
    'Portugal': 'Portugal', 'Hungary': 'Hungary', 'Czech Republic': 'Czechia',
    'Israel': 'Israel', 'Canada': 'Canada', 'Ontario': 'Canada',
    'Quebec': 'Canada', 'QC': 'Canada', 'British Columbia': 'Canada',
    'BC': 'Canada',
    'Australia': 'Australia', 'NSW': 'Australia',
    'Japan': 'Japan', 'China': 'China', 'South Korea': 'South Korea',
    'Korea': 'South Korea', 'Singapore': 'Singapore', 'India': 'India',
    'Brazil': 'Brazil', 'United Arab Emirates': 'UAE', 'UAE': 'UAE',
    'Cayman Islands': 'Cayman Islands', 'Macedonia': 'North Macedonia',
    'New Zealand': 'New Zealand',
}

REGION_MAP = {
    'USA': 'North America', 'Canada': 'North America',
    'UK': 'Europe', 'France': 'Europe', 'Germany': 'Europe', 'Italy': 'Europe',
    'Spain': 'Europe', 'Switzerland': 'Europe', 'Netherlands': 'Europe',
    'Belgium': 'Europe', 'Ireland': 'Europe', 'Sweden': 'Europe',
    'Denmark': 'Europe', 'Norway': 'Europe', 'Finland': 'Europe',
    'Austria': 'Europe', 'Lithuania': 'Europe', 'Poland': 'Europe',
    'Portugal': 'Europe', 'Hungary': 'Europe', 'Czechia': 'Europe',
    'North Macedonia': 'Europe',
    'Israel': 'MENA', 'UAE': 'MENA',
    'Japan': 'Asia', 'China': 'Asia', 'South Korea': 'Asia',
    'Singapore': 'Asia', 'India': 'Asia',
    'Australia': 'Oceania', 'New Zealand': 'Oceania',
    'Brazil': 'LATAM',
    'Cayman Islands': 'Other',
}


def derive_country(loc: str) -> str:
    if not loc:
        return ''
    loc = loc.strip()
    # Check last comma-separated token
    parts = [p.strip() for p in re.split(r'[,;]', loc) if p.strip()]
    if not parts:
        return ''
    # Check tokens from last to first
    for tok in reversed(parts):
        if tok in COUNTRY_MAP:
            return COUNTRY_MAP[tok]
        # Try last word too (for state codes)
        last = tok.split()[-1] if tok.split() else tok
        if last in COUNTRY_MAP:
            return COUNTRY_MAP[last]
    return parts[-1]  # fallback: just use the last token


def derive_modality(industries: list) -> str:
    """Try to infer primary modality from industry tags + name hints."""
    ind_lower = [i.lower() for i in industries]
    ind_str = ' '.join(ind_lower)
    if 'wearables' in ind_str or 'wearable' in ind_str:
        return 'Wearable'
    if 'hardware' in ind_str:
        return 'Hardware'
    if any('ai/ml' in i or 'ai ml' in i or 'data analytics' in i for i in ind_lower):
        return 'Software/AI'
    if 'research tools' in ind_str:
        return 'Research Tools'
    if 'therapeutics' in ind_str:
        return 'Therapeutics'
    if 'diagnostics' in ind_str:
        return 'Diagnostics'
    if 'medical devices' in ind_str:
        return 'Medical Device'
    return 'Other'


def derive_application(industries: list) -> str:
    ind_str = ' '.join(i.lower() for i in industries)
    # Priority order
    if 'clinical research' in ind_str or 'therapeutics' in ind_str:
        return 'Medical/Therapeutic'
    if 'medical devices' in ind_str and ('diagnostics' in ind_str or 'digital health' in ind_str):
        return 'Medical/Diagnostic'
    if 'wellness' in ind_str or 'consumer electronics' in ind_str:
        return 'Consumer/Wellness'
    if 'research tools' in ind_str:
        return 'Research Tools'
    if 'ai/ml' in ind_str or 'software/saas' in ind_str or 'data analytics' in ind_str:
        return 'Software/Analytics'
    if 'medical devices' in ind_str:
        return 'Medical/Device'
    return 'Other'


def derive_invasiveness(industries: list, name: str) -> str:
    ind = ' '.join(i.lower() for i in industries)
    n = name.lower()
    # Explicit BCI/implant-heavy companies
    implant_keywords = [
        'neuralink', 'synchron', 'paradromics', 'blackrock', 'precision neuro',
        'motif neuro', 'iota', 'inbrain', 'science corp', 'science ',
        'phantom neuro', 'mintneuro', 'axoft', 'neurobionics',
        'neurostar', 'neuroone', 'neuralled', 'bluewind', 'cadence',
        'subsense', 'onward medical', 'nalu', 'neuspera', 'saluda',
        'inner cosmos', 'iota biosciences', 'presidio medical',
        'neurolutions', 'valencia tech', 'livanova',
    ]
    if any(k in n for k in implant_keywords):
        return 'Invasive'
    if 'wearables' in ind or 'consumer electronics' in ind:
        return 'Non-invasive'
    if 'research tools' in ind and 'medical devices' not in ind:
        return 'Non-invasive'
    if 'therapeutics' in ind and 'medical devices' in ind:
        return 'Mixed/Unknown'
    return 'Non-invasive'  # default for non-medical-device rows


def normalize_headcount(hc: str) -> str:
    if not hc:
        return ''
    hc = hc.strip().lower().replace('c_', '').replace('_', '-')
    # c_00001_00010 -> 00001-00010 -> 1-10
    m = re.match(r'^(\d+)-(\d+)$', hc)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return f'{a}-{b}'
    return hc


def lookup_founding(name: str) -> tuple:
    n = name.lower().strip()
    if n in FOUNDING:
        return FOUNDING[n]
    # Try partial matches
    for k, v in FOUNDING.items():
        if k in n or n in k:
            return v
    return (None, '')


def parse_raw(path: Path) -> list:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                continue
            parts = line.split('|')
            if len(parts) < 7:
                parts += [''] * (7 - len(parts))
            name, ind, hc, lf, web, loc, jobs = parts[:7]
            industries = [i.strip() for i in ind.split(';') if i.strip()]
            rows.append({
                'name': name.strip(),
                'industries_raw': ind,
                'industries_list': industries,
                'headcount_raw': hc,
                'last_funding': lf.strip(),
                'website': web.strip(),
                'location': loc.strip(),
                'live_jobs': jobs.strip(),
            })
    return rows


def build(rows: list) -> list:
    out = []
    for r in rows:
        country = derive_country(r['location'])
        region = REGION_MAP.get(country, '')
        modality = derive_modality(r['industries_list'])
        application = derive_application(r['industries_list'])
        invasiveness = derive_invasiveness(r['industries_list'], r['name'])
        year, conf = lookup_founding(r['name'])
        half = ''
        decade = ''
        if year:
            decade = f'{(year // 10) * 10}s'
            half = f'{year}-H1'  # default — we don't have month granularity
        out.append({
            'name': r['name'],
            'website': r['website'],
            'location': r['location'],
            'country': country,
            'region': region,
            'industries': r['industries_raw'],
            'primary_modality': modality,
            'application': application,
            'invasiveness': invasiveness,
            'headcount_bucket': normalize_headcount(r['headcount_raw']),
            'last_funding_stage': r['last_funding'],
            'live_jobs': r['live_jobs'],
            'founding_year': year if year else '',
            'founding_confidence': conf,
            'decade': decade,
            'half_year': half,
        })
    return out


def main():
    rows = parse_raw(RAW)
    print(f'Parsed {len(rows)} rows')
    enriched = build(rows)

    # dedupe by name keeping first
    seen = set()
    dedup = []
    for r in enriched:
        k = r['name'].lower()
        if k in seen:
            continue
        seen.add(k)
        dedup.append(r)
    print(f'After dedupe: {len(dedup)}')

    with OUT_CSV.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(dedup[0].keys()))
        w.writeheader()
        w.writerows(dedup)
    print(f'Wrote {OUT_CSV}')

    # quick stats
    with_year = sum(1 for r in dedup if r['founding_year'])
    print(f'Founding year coverage: {with_year}/{len(dedup)} = {100*with_year/len(dedup):.1f}%')
    # country coverage
    with_country = sum(1 for r in dedup if r['country'])
    print(f'Country coverage: {with_country}/{len(dedup)} = {100*with_country/len(dedup):.1f}%')
    # Top countries
    from collections import Counter
    cc = Counter(r['country'] for r in dedup if r['country'])
    print('Top countries:', cc.most_common(10))
    rc = Counter(r['region'] for r in dedup if r['region'])
    print('By region:', dict(rc))
    # Year histogram (known)
    yc = Counter(r['founding_year'] for r in dedup if r['founding_year'])
    print('Years present:', sorted(yc.keys()))


if __name__ == '__main__':
    main()
