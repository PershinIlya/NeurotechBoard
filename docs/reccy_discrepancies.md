# reccy.dev discrepancies

Cases where web research contradicts the reccy.dev listing. We **keep reccy's values** in the CSV as-is (reccy is the authoritative source), but track the disagreement here so we can revisit during v0.2.0+.

## Wrong-entity scrapes

### Mad Science Group Inc. — not neurotech at all, it's a kids' STEM franchise

- **reccy says:** Mad Science Group Inc., Canada, categorized as neurotech
- **Web finds:** Mad Science Group is a Quebec-based children's STEM education franchise (after-school programs, birthday parties, summer camps), founded ~1985. No connection to neurotech.
- **Likely confusion:** There is a separate US neurotech company called **Madison Scientific (MadSci)** (madsci.com) that makes hydrocephalus shunts — reccy may have confused the two, or picked up the wrong "Mad Science" when crawling.
- **Decision:** keep the row (we trust reccy's inclusion list), keep founding_year = 1985 (correct for the Canadian STEM company), but flag here that this entity almost certainly does not belong in a neurotech dataset. Candidate for removal in v0.3.0 when we do a pass of "is this actually neurotech?" cleanups.

## Duplicate rows

### Glneurotech == Great Lakes NeuroTechnologies

- **reccy says:** two separate rows — `Glneurotech` and `Great Lakes NeuroTechnologies`, both Ohio/USA, both with `glneurotech.com`.
- **Web finds:** same company. "GLneurotech" is just the short domain form of "Great Lakes NeuroTechnologies Inc." Founded 2011 as a spin-off from Cleveland Medical Devices Inc.
- **Source:** https://www.glneurotech.com/blog/2011/03/23/press-release-cleveland-medical-devices-inc-spins-off-great-lakes-neurotechnologies/
- **Decision:** both rows get founding_year = 2011 (H). Previous v0.1.x values (1994 L) were wrong — 1994 was the founding of the *parent* Cleveland Medical Devices, not the independent spin-off. Both rows are candidates for dedup in v0.3.0.

## huMannity Medtec — confidence downgrade (2026-04-09)

- **v0.1.3 initial value:** `(1985, 'H')` — used the Alfred Mann Foundation year because huMannity Medtec is a rebrand of that foundation.
- **Issue:** 1985 is the *parent foundation's* founding, not the rebrand year. The rebrand happened much later (unknown exact date), and claiming 1985 as founding_year with H confidence is misleading. The 2014 lifelines chart in v0.2.0+ made this visible — the row anchored all the way in 1985, looking like a legacy player, which it isn't.
- **v0.2.1 fix:** downgraded to `(1985, 'L')` — year kept because Alfred Mann Foundation IS the parent, but confidence downgraded to reflect that this is really a proxy for "unknown rebrand year, at least this old". Proper fix would be to find the actual rebrand year and use that with H confidence, or drop the year entirely. Deferred.

## Country / entity mismatches

### Neuromark — listed as USA, actually Ireland (Neurent Medical)

- **reccy says:** Neuromark, USA
- **Web research finds:** "Neuromark" is a product, not a company. The developer is **Neurent Medical**, founded 2015 in Galway, Ireland.
- **Source:** https://www.crunchbase.com/organization/neurent-medical
- **Decision for v0.1.x:** founding_year = 2015 (confidence H, source: Crunchbase). `country` left as USA per reccy. Flagged here for resolution in v0.2.0.
- **Open question:** Should we rename rows in our CSV to match legal entity, or preserve reccy's product-based naming?

### Manava — listed as Switzerland, actually Italy

- **reccy says:** Manava, Switzerland
- **Web finds:** Milan, Italy (spinal cord BCI, founded 2022)
- **Source:** https://www.crunchbase.com/organization/manava-plus
- **Decision:** country kept as Switzerland per reccy, founding_year = 2022 (H).

### Mave — listed with no country, actually India

- **reccy says:** Mave, no country
- **Web finds:** Bengaluru, India (founded 2023)
- **Source:** https://www.crunchbase.com/organization/mave-health
- **Decision:** country left blank (not in COUNTRY_MAP); founding_year = 2023 (H). To backfill in country enrichment pass.

### Journey-frame — listed as USA, actually UK

- **reccy says:** Journey-frame, USA
- **Web finds:** Product of Phantom Technology, Cambridge UK (parent founded 2019)
- **Source:** https://www.crunchbase.com/organization/phantom-technology
- **Decision:** country kept as USA per reccy, founding_year = 2019 (M).

### EnterTech, Inc — listed as USA, actually China

- **reccy says:** EnterTech, Inc, USA
- **Web finds:** Hangzhou, China (Flowtime headband, founded 2014)
- **Source:** https://global.chinadaily.com.cn/a/202512/11/WS693a2979a310d6866eb2e135.html
- **Decision:** country kept as USA per reccy, founding_year = 2014 (M).

### Grey Matter Neuropsychology of New York — listed as Canada, actually NYC USA

- **reccy says:** country Canada
- **Web finds:** NYC-based practice (no reliable founding year found)
- **Decision:** country kept as Canada per reccy, founding_year SKIP.

### Cerevia — listed as France, actually USA (Maryland)

- **reccy says:** Cerevia, France
- **Web finds:** Cerevia Neurosciences, Rockville MD — a Weinberg Medical Physics spinout, founded 2025. (The French "Cérévia" is an unrelated agricultural cooperative.)
- **Source:** https://cerevia.care/
- **Decision:** country kept as France per reccy, founding_year = 2025 (H).

### Brain Technologies, Inc. — listed as USA, actually Israel (Brain.Space)

- **reccy says:** Brain Technologies, Inc., USA
- **Web finds:** Brain.Space, Israel (founded 2018), neuro-wellness wearable.
- **Source:** https://www.brain.space/
- **Decision:** country kept as USA per reccy, founding_year = 2018 (M).

### Nuro Inc — Canadian neurotech, NOT the self-driving Nuro

- **reccy says:** Nuro Inc, Canada
- **Web finds:** NURO Corp, Waterloo Canada (founded 2016) — BCI / neurotech company, distinct from the much-better-known Nuro self-driving robotics company (USA, 2016). Easy to confuse.
- **Source:** https://www.crunchbase.com/organization/nuro-corp
- **Decision:** founding_year = 2016 (H). No country mismatch, just a name-collision worth flagging.

### nmtc1 == NeuroOne Medical (duplicate row in reccy)

- **reccy says:** two separate rows — `NeuroOne Medical` and `Nmtc1`, both Eden Prairie MN, both website nmtc1.com.
- **Web finds:** Same company. NMTC1 is the ticker. NeuroOne Medical Technologies Corp, founded 2009 (H).
- **Decision:** both rows get founding_year = 2009. Candidate for dedup in v0.2.0.

### huMannity Medtec — uses parent foundation year (1985)

- **reccy says:** huMannity Medtec, USA
- **Web finds:** Rebrand of Alfred Mann Foundation (founded 1985). The current rebranded entity's first-mention date is not publicly documented.
- **Source:** https://www.humannitymedtec.org/
- **Decision:** founding_year = 1985 (H), but flagged here because this is a parent-foundation date, not a "current entity" date. Compare to Bioness/Bioventus pattern.

### Dusq — listed as Netherlands, actually India

- **reccy says:** Dusq, Haarlem, Noord-Holland, website `dusq.com`
- **Web finds:** DUSQ is a sleep-science startup headquartered in India (formerly InnerGize, known from Shark Tank India). Founded 2023 by Dr. Siddhant Bhargava, Shalmali Kadu, and Mitansh Khurana. Raised ₹24 crore seed in Feb 2026 from Fireside Ventures, Antler India, etc. Fully on-topic as neurotech.
- **Source:** https://www.business-standard.com/content/press-releases-ani/indian-sleep-science-startup-dusq-formerly-innergize-raises-24-cr-to-challenge-global-sleep-tech-leaders-126021600674_1.html
- **Decision:** founding_year = 2023 (H). country kept as Netherlands per reccy. Candidate for country fix in v0.2.0.
- **Note (v0.1.2 error, corrected in v0.1.3):** The v0.1.2 release initially classified Dusq as "sustainable baby clothing" with founding_year 2018. This was wrong — the researcher went to `dusq.nl` (an unrelated Dutch clothing brand) instead of `dusq.com` (the actual reccy-listed company). Root cause: blindly matching company name to a `.nl` domain because the reccy row said Netherlands. Lesson: always use the exact `website` field from reccy, not the country-implied TLD.

## v0.1.3 lookup-key bug class

A whole class of dict-key bugs surfaced during round 2 enrichment: when the raw company name contains a non-ASCII letter, Python's `str.lower()` produces lowercase **including the diacritic** — but the hardcoded FOUNDING dict keys had been written with ASCII letters or wrong-cased macron letters. The lookup `.lower()` of the raw name silently failed to find the key, and the row stayed empty even though we "had" data.

| Row | Raw name | Wrong key | Correct key |
|---|---|---|---|
| Oura Ring | `ŌURA` | `ŌURA` (uppercase) | `ōura` |
| Bía Neuroscience | `Bía Neuroscience` | `bia neuroscience` (no accent) | `bía neuroscience` |
| huMannity Medtec | `huMannity Medtec` | `huMannity medtec` (camelcase) | `humannity medtec` |

All three were fixed in v0.1.3. Lesson: when adding entries by hand, always lowercase the raw name in Python first (`name.lower()`) and paste *that* as the key.

## v0.1.0 quality fixes (post-release)

Bugs found in the hardcoded FOUNDING dict's partial-match fallback during pilot research:

| Company | v0.1.0 matched to | v0.1.0 year | Correct |
|---|---|---|---|
| Syndeio Biosciences | `bios` (wrong company) | 2015 (M) | unknown — removed |
| Axo | `muse by interaxon` (wrong) | 2007 (H) | unknown — removed |
| NeuroMind AGI | `neuromind` (France, wrong) | 2022 (M) | unknown — kept as SKIP |

Fix: `lookup_founding` now requires exact key match. Paradromics, Inc. and 株式会社LIFESCAPES added as explicit keys so they still resolve correctly.
