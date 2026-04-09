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
    'paradromics, inc.': (2015, 'H'),
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
    '株式会社lifescapes': (2019, 'L'),
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
    # ---- Web-researched batch 1 (2026-04-09) ----
    'optohive': (2023, 'H'),
    'omnipemf': (2016, 'H'),
    'nueyne': (2017, 'H'),
    'nimbus': (2024, 'M'),
    'nexalin technology': (2010, 'H'),
    'newrotex': (2019, 'H'),
    'neuroview technology': (2016, 'H'),
    'neuroverse': (2012, 'H'),
    'neurosync': (2022, 'M'),
    'neuro-stellar': (2021, 'H'),
    'neuroservo': (2015, 'H'),
    'neuroone medical': (2009, 'H'),
    'neuro rehab vr': (2017, 'M'),
    'neuronostics': (2018, 'H'),
    'neuronoff': (2017, 'M'),
    'neurofenix': (2016, 'H'),
    'neurode': (2021, 'H'),
    'neurobell': (2023, 'H'),
    'neuromind': (2022, 'M'),
    'neurinnov': (2018, 'H'),
    'neuromark': (2015, 'H'),  # actually Neurent Medical (IE), see reccy_discrepancies.md
    'neurology care platform': (2022, 'H'),
    'affectablesleep': (2020, 'L'),
    'neumarker': (2022, 'H'),
    # ---- Web-researched batch 2 (2026-04-09, v0.1.2) ----
    'neuronexus': (2004, 'H'),
    'nyx-tech': (2016, 'H'),
    'marbles health': (2020, 'H'),
    'acoustiic': (2017, 'M'),
    'naqi logix': (2020, 'H'),
    'epia neuro': (2026, 'H'),
    'intheon': (2015, 'M'),
    'linkedin': (2026, 'M'),  # reccy mislabeled — actually Temple by Deepinder Goyal
    'clee medical': (2024, 'H'),
    'evon medics': (2013, 'H'),
    'brainpatch®': (2018, 'H'),
    'mynd immersive': (2016, 'H'),
    'monteris': (1999, 'H'),
    'modality.ai': (2018, 'H'),
    'mobio interactive': (2015, 'H'),
    'moberg analytics': (2020, 'H'),
    'mjn-neuro': (2014, 'H'),
    'getenophone': (2016, 'M'),
    'mindrove': (2016, 'M'),
    'mindaffect': (2017, 'H'),
    'alphaomega': (1993, 'H'),
    'methinks ai stroke solutions': (2016, 'H'),
    'metaphysiks': (2016, 'M'),
    'mesmerise group': (2016, 'H'),
    'melo': (2021, 'M'),  # built by Decently Ltd
    'mxwbio': (2016, 'H'),  # MaxWell Biosystems, ETH Zurich spin-off
    'manava': (2022, 'H'),  # actually Italy, not Switzerland
    'magnusmed': (2020, 'H'),
    'optoceutics': (2018, 'H'),
    'brainlink by macrotellect': (2010, 'M'),  # parent Macrotellect
    'machine medicine': (2017, 'H'),
    'lotus neuro': (2025, 'H'),  # Insightec spinout
    'longeviti': (2016, 'H'),
    'mave': (2023, 'H'),  # India, no country in reccy
    'journey-frame': (2019, 'M'),  # parent Phantom Technology, UK not USA
    'keywise': (2019, 'H'),
    'karavela': (2025, 'H'),
    'restera': (2020, 'H'),  # formerly Invicta Medical
    'we are brain imaging specialists imeka™': (2011, 'H'),
    'homneuro': (2024, 'M'),
    'cogwear': (2018, 'H'),
    'healios.org': (2013, 'H'),
    'harmoneyes': (2012, 'M'),
    'gowerlabs': (2013, 'H'),
    '格式塔科技 (gestala)': (2026, 'H'),
    'dusq': (2018, 'M'),  # actually sustainable clothing brand, not neurotech
    'dixi medical': (1988, 'H'),
    'diagnostic biochips, inc.': (2013, 'H'),
    'inflammasense': (2021, 'M'),
    'boomerang medical, inc.': (2021, 'H'),
    'bluearbortech': (2023, 'M'),
    'bioness medical': (2004, 'H'),  # Bioventus subsidiary since 2021
    'biocurrent': (2022, 'H'),
    'holbergeeg': (2009, 'H'),
    '格式塔科技 (gestala) 2': (2026, 'H'),  # duplicate row in reccy
    'focuscalm': (2015, 'H'),  # parent BrainCo
    'fareon, inc.': (2019, 'H'),  # formerly Humanity Neurotech
    'eyetronic': (2007, 'H'),
    'evoke neuroscience': (2009, 'H'),
    'entertech, inc': (2014, 'M'),  # China, not USA
    'enspire dbs therapy, inc.': (2012, 'M'),
    'encora therapeutics': (2018, 'H'),
    'enchannel medical': (2020, 'H'),
    'emvision': (2017, 'H'),
    'emteq labs': (2015, 'H'),
    'e184': (2023, 'M'),
    'spryte medical': (2023, 'H'),
    'stimaire': (2017, 'H'),
    'stimvia': (2014, 'H'),  # originally Tesla Medical
    'stratus neuro': (2006, 'H'),
    'supermind platforms, inc': (2020, 'M'),
    'join.synchneuro': (2021, 'H'),
    'syndeio biosciences': (2025, 'H'),
    'synerfuse': (2015, 'M'),
    'synergiamedical.com': (2014, 'M'),
}

# Source attribution for founding_year. Entries not in this dict default to
# 'training_knowledge' — the v0.1.0 hardcoded dict was populated from model
# training knowledge, not web-verified. New web-researched entries carry their
# actual source URL(s) here.
SOURCES = {
    'optohive': 'https://www.cbinsights.com/company/optohive',
    'omnipemf': 'https://www.cbinsights.com/company/omnipemf',
    'nueyne': 'https://www.crunchbase.com/organization/nueyne',
    'nimbus': 'https://www.linkedin.com/company/nimbusbci',
    'nexalin technology': 'https://www.crunchbase.com/organization/nexalin-technology',
    'newrotex': 'https://find-and-update.company-information.service.gov.uk/company/11798939',
    'neuroview technology': 'https://www.crunchbase.com/organization/neuroview-technology',
    'neuroverse': 'https://www.crunchbase.com/organization/neuroverse',
    'neurosync': 'https://www.neurosync.health/about/',
    'neuro-stellar': 'https://tracxn.com/d/legal-entities/india/neurostellar-private-limited/',
    'neuroservo': 'https://www.crunchbase.com/organization/neuroservo',
    'neuroone medical': 'https://www.crunchbase.com/organization/neuroone-medical-technologies-corp',
    'neuro rehab vr': 'https://www.crunchbase.com/organization/neuro-rehab-vr',
    'neuronostics': 'https://www.neuronostics.com/history/',
    'neuronoff': 'https://www.cbinsights.com/company/neuronoff',
    'neurofenix': 'https://www.crunchbase.com/organization/neurofenix',
    'neurode': 'https://www.crunchbase.com/organization/neurode',
    'neurobell': 'https://www.enterprise-ireland.com/en/news/mark-o-sullivan-neurobell-announced-as-founder-of-the-year-2025',
    'neuromind': 'https://www.neuromind.fr/',
    'neurinnov': 'https://neurinnov.com/about-neurinnov/',
    'neuromark': 'https://www.crunchbase.com/organization/neurent-medical',
    'neurology care platform': 'https://www.cbinsights.com/company/neu-health',
    'affectablesleep': 'https://www.affectablesleep.com/about',
    'neumarker': 'https://www.cbinsights.com/company/neumarker',
    # ---- Web-researched batch 2 (2026-04-09, v0.1.2) ----
    'neuronexus': 'https://www.crunchbase.com/organization/neuronexus-technologies',
    'nyx-tech': 'https://finder.startupnationcentral.org/company_page/nyx-technologies',
    'marbles health': 'https://tracxn.com/d/companies/marbles/__7Bc-5-Ke4TJ0Tp28elgJy5RoT6nb5YJUN508jOtsdl4',
    'acoustiic': 'https://www.crunchbase.com/organization/acoustiic-inc',
    'naqi logix': 'https://www.sec.gov/Archives/edgar/data/1902337/000106299324019659/form1a.htm',
    'epia neuro': 'https://www.businesswire.com/news/home/20260402282679/en/Epia-Neuro-Launches-to-Develop-Intent-Driven-Neural-Technology-to-Restore-Function-After-Stroke-and-Address-Cognitive-Decline',
    'intheon': 'https://www.crunchbase.com/organization/intheon',
    'linkedin': 'https://techfundingnews.com/deepinder-goyal-temple-54m-brain-wearable-funding/',
    'clee medical': 'https://www.cleemedical.com/news/2024/11/24/clee-medical-birth.html',
    'evon medics': 'https://www.crunchbase.com/organization/evon-medics',
    'brainpatch®': 'https://brainpatch.ai/about',
    'mynd immersive': 'https://pitchbook.com/profiles/company/264330-19',
    'monteris': 'https://www.monteris.com/about-monteris/',
    'modality.ai': 'https://modality.ai/about',
    'mobio interactive': 'https://www.crunchbase.com/organization/mobio-interactive',
    'moberg analytics': 'https://moberganalytics.com/about-us/story/',
    'mjn-neuro': 'https://mjn.cat/en/team/',
    'getenophone': 'https://getenophone.com/',
    'mindrove': 'https://pitchbook.com/profiles/company/225664-84',
    'mindaffect': 'https://www.crunchbase.com/organization/mindaffect',
    'alphaomega': 'https://www.alphaomega-eng.com/Company-Overview',
    'methinks ai stroke solutions': 'https://www.crunchbase.com/organization/methinks-2e94',
    'metaphysiks': 'https://pitchbook.com/profiles/company/459255-61',
    'mesmerise group': 'https://pitchbook.com/profiles/company/268149-16',
    'melo': 'https://businesscloud.co.uk/news/startup-behind-nhs-patient-safety-software-raises-500k/',
    'mxwbio': 'https://bsse.ethz.ch/bel/spin-offs/maxwell-biosystems-ag.html',
    'manava': 'https://www.crunchbase.com/organization/manava-plus',
    'magnusmed': 'https://www.magnusmed.com/press-release/magnus-medical-launch/',
    'optoceutics': 'https://www.crunchbase.com/organization/optoceutics',
    'brainlink by macrotellect': 'https://www.crunchbase.com/organization/macrotellect',
    'machine medicine': 'https://find-and-update.company-information.service.gov.uk/company/10787420',
    'lotus neuro': 'https://insightec.com/news/insightec-announces-spin-out-of-lotus-neuro-to-advance-focused-ultrasound-brain-therapies/',
    'longeviti': 'https://www.crunchbase.com/organization/longeviti',
    'mave': 'https://www.crunchbase.com/organization/mave-health',
    'journey-frame': 'https://www.crunchbase.com/organization/phantom-technology',
    'keywise': 'https://www.crunchbase.com/organization/keywise-ai',
    'karavela': 'https://www.crunchbase.com/organization/karavela-2bb8',
    'restera': 'https://www.resterasleep.com/invicta-25m-series-a',
    'we are brain imaging specialists imeka™': 'https://imeka.ca/about/',
    'homneuro': 'https://www.dmagazine.com/healthcare-business/2026/02/how-dallas-based-startup-hom-neuro-is-making-testing-for-epilepsy-and-seizures-more-accessible/',
    'cogwear': 'https://www.crunchbase.com/organization/cogwear-technologies',
    'healios.org': 'https://healios.org.uk/about/',
    'harmoneyes': 'https://pitchbook.com/profiles/company/741168-10',
    'gowerlabs': 'https://www.ucl.ac.uk/impact/case-studies/2022/apr/gowerlabs-advancing-optical-brain-imaging-neuroscience-applications-industry',
    '格式塔科技 (gestala)': 'https://m.tech.china.com/redian/2026/0105/012026_1792327.html',
    'dusq': 'https://dusq.nl/en/about/',
    'dixi medical': 'https://diximedical.com/about',
    'diagnostic biochips, inc.': 'https://diagnosticbiochips.com/our-story',
    'inflammasense': 'https://pitchbook.com/profiles/company/522913-78',
    'boomerang medical, inc.': 'https://www.crunchbase.com/organization/boomerang-medical',
    'bluearbortech': 'https://tracxn.com/d/companies/blue-arbor-technologies/__k0L3VSinWOt1vVXIGokCylDE1nBEcni4NWQ-HTn6ynE',
    'bioness medical': 'https://uk.bioness.com/About_Us.php',
    'biocurrent': 'https://www.crunchbase.com/organization/biocurrent',
    'holbergeeg': 'https://www.crunchbase.com/organization/holberg-eeg-as',
    '格式塔科技 (gestala) 2': 'https://techcrunch.com/2026/03/11/bci-startup-gestala-raises-21-million-for-non-invasive-ultrasound-brain-tech/',
    'focuscalm': 'https://en.wikipedia.org/wiki/BrainCo',
    'fareon, inc.': 'https://pitchbook.com/profiles/company/553947-22',
    'eyetronic': 'https://pitchbook.com/profiles/company/57224-08',
    'evoke neuroscience': 'https://www.crunchbase.com/organization/evoke-neuroscience',
    'entertech, inc': 'https://global.chinadaily.com.cn/a/202512/11/WS693a2979a310d6866eb2e135.html',
    'enspire dbs therapy, inc.': 'https://pitchbook.com/profiles/company/168052-60',
    'encora therapeutics': 'https://www.crunchbase.com/organization/encora',
    'enchannel medical': 'https://enchannel.com/about/',
    'emvision': 'https://emvision.com.au/about/',
    'emteq labs': 'https://find-and-update.company-information.service.gov.uk/company/09708880',
    'e184': 'https://pitchbook.com/profiles/investor/616284-73',
    'spryte medical': 'https://www.linkedin.com/company/spryte-medical',
    'stimaire': 'https://www.crunchbase.com/organization/stimaire',
    'stimvia': 'https://www.stimvia.com/en/press/press-releases/',
    'stratus neuro': 'https://www.stratusneuro.com/about',
    'supermind platforms, inc': 'https://www.linkedin.com/in/chad-olin/',
    'join.synchneuro': 'https://pitchbook.com/profiles/company/606687-85',
    'syndeio biosciences': 'https://cen.acs.org/business/start-ups/Syndeio-Biosciences-launches-molecules-target/103/web/2025/05',
    'synerfuse': 'https://www.crunchbase.com/organization/synerfuse',
    'synergiamedical.com': 'https://www.crunchbase.com/organization/synergia-medical',
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
    """Return (year, confidence, source). source defaults to 'training_knowledge'
    for entries in FOUNDING without an explicit SOURCES entry.

    Exact key match only. Partial/substring matching used to cause false hits
    (e.g. 'NeuroMind AGI' matching 'neuromind'); legitimate name variants must
    be added as explicit keys.
    """
    n = name.lower().strip()
    if n not in FOUNDING:
        return (None, '', '')
    year, conf = FOUNDING[n]
    source = SOURCES.get(n, 'training_knowledge')
    return (year, conf, source)


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
        year, conf, source = lookup_founding(r['name'])
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
            'founding_year_source': source,
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
