# Data Extraction Task: Extract Entities from Scholarly Works

## Your Mission

Extract **historical persons**, **historical works**, and **places** that are mentioned in scholarly work titles and bibliographic entries. The scholarly works themselves are the raw data source.

---

## Input Data

You will receive bibliographic entries for scholarly works in this format:

```
DAVIDSON, HERBERT. Moses Maimonides, The Man and His Works. Oxford: Oxford University Press, 2004.
KELLNER, MENACHEM. Maimonides' Confrontation with Mysticism. Oxford: Littman Library, 2006.
FELDMAN, SEYMOUR. Platonic Cosmologies in the Dialoghi d'Amore of Leone Ebreo (Judah Abravanel). 2005.
HARVEY, STEVEN. Arabic into Hebrew: the Hebrew Translation Movement and the Influence of Averroes upon Medieval Jewish Thought.
LOBEL, DIANA. Ittisal and the Amr Ilahi: Divine Immanence and the World to Come in the Kuzari. 2006.
```

---

## Output Required

Create **3 CSV files**:

### 1. `persons_extracted.csv`
Historical persons mentioned in the titles

### 2. `works_extracted.csv`
Historical works mentioned in the titles

### 3. `places_extracted.csv`
Places mentioned in the titles or publication info

---

## CSV Schemas

**IMPORTANT**: You do NOT need to create IDs. Just extract the data - IDs will be assigned later during import.

### 1. Persons CSV (`persons_extracted.csv`)

| Column | Required | Description | Example |
|--------|----------|-------------|---------|
| `name` | ✅ Yes | Person's name as mentioned | `Moses Maimonides` |
| `wikidata_qid` | ⚠️ If available | Wikidata QID | `Q127398` |
| `birth_year` | ⚠️ If available | From Wikidata | `1138` |
| `death_year` | ⚠️ If available | From Wikidata | `1204` |
| `birth_place_qid` | ⚠️ If available | Wikidata QID of birthplace | `Q5818` |
| `death_place_qid` | ⚠️ If available | Wikidata QID of death place | `Q85` |

**Example:**
```csv
name,wikidata_qid,birth_year,death_year,birth_place_qid,death_place_qid
Moses Maimonides,Q127398,1138,1204,Q5818,Q85
Gersonides,Q310862,1288,1344,Q271093,Q6730
Judah Abravanel,Q311226,1460,1521,Q597,
Leone Ebreo,,,,,
```

---

### 2. Works CSV (`works_extracted.csv`)

| Column | Required | Description | Example |
|--------|----------|-------------|---------|
| `title` | ✅ Yes | Work title as mentioned | `Guide for the Perplexed` |
| `author_name` | ⚠️ If known | Author's name (will be linked later) | `Moses Maimonides` |
| `language` | ⚠️ If available | Original language | `Arabic` |
| `wikidata_qid` | ⚠️ If available | Wikidata QID | `Q60736` |

**Example:**
```csv
title,author_name,language,wikidata_qid
Guide for the Perplexed,Moses Maimonides,Arabic,Q60736
Mishneh Torah,Moses Maimonides,Hebrew,Q748909
The Kuzari,Judah Halevi,Arabic,Q944985
Dialoghi d'Amore,Judah Abravanel,Italian,
```

---

### 3. Places CSV (`places_extracted.csv`)

| Column | Required | Description | Example |
|--------|----------|-------------|---------|
| `name` | ✅ Yes | Place name | `Oxford` |
| `wikidata_qid` | ✅ **REQUIRED** | Wikidata QID | `Q34217` |
| `coordinates` | ✅ **REQUIRED** | "lat,lon" format | `"51.7520,-1.2577"` |
| `type` | ⚠️ Optional | publication_place or historical_place | `publication_place` |

**Example:**
```csv
name,wikidata_qid,coordinates,type
Oxford,Q34217,"51.7520,-1.2577",publication_place
Cordoba,Q5818,"37.8882,-4.7794",historical_place
Cairo,Q85,"30.0444,31.2357",historical_place
```

---

## Extraction Rules

### For Persons:

**Look for person names in titles that indicate the work is ABOUT that person:**

✅ **Extract these patterns:**
- "Moses Maimonides, The Man and His Works" → Extract: `Moses Maimonides`
- "Maimonides' Confrontation with Mysticism" → Extract: `Maimonides`
- "Leone Ebreo (Judah Abravanel)" → Extract both: `Leone Ebreo` AND `Judah Abravanel`
- "Gersonides' Accounts of Prophecy" → Extract: `Gersonides`
- "Judah Halevi's Political Philosophy" → Extract: `Judah Halevi`

❌ **Don't extract:**
- Modern authors (DAVIDSON, KELLNER, etc.)
- Generic references ("medieval philosophers", "Jewish thinkers")

**For each person:**
1. Search Wikidata for their QID
2. If found, extract birth/death years and places from Wikidata
3. If not found, leave those fields empty

---

### For Works:

**Look for titles of historical works mentioned:**

✅ **Extract these patterns:**
- "the Kuzari" → Extract: `The Kuzari`
- "Guide for the Perplexed" → Extract: `Guide for the Perplexed`
- "Dialoghi d'Amore" → Extract: `Dialoghi d'Amore`
- "Mishneh Torah" → Extract: `Mishneh Torah`
- "Wars of the Lord" → Extract: `Wars of the Lord`

**Clues that it's a historical work:**
- Italicized or in quotes in the original
- Well-known medieval titles
- Associated with a historical person

**For each work:**
1. Search Wikidata for the work
2. Extract author ID (link to person from persons CSV)
3. Extract language if available in Wikidata
4. If not in Wikidata, leave optional fields empty

---

### For Places:

**Extract TWO types of places:**

**Type 1: Publication Places** (from bibliographic info)
- "Oxford: Oxford University Press" → Extract: `Oxford`
- "Frankfurt: Peter Lang" → Extract: `Frankfurt`
- Usually appears before the publisher name

**Type 2: Historical Places** (mentioned in titles)
- "Bagdad und Jerusalem als Städte..." → Extract: `Baghdad`, `Jerusalem`
- Geographic references in titles about historical events/persons

**For each place:**
1. **MUST** search Wikidata for QID
2. **MUST** extract coordinates from Wikidata (Property P625)
3. Format coordinates as `"lat,lon"` with quotes
4. Mark type as `publication_place` or `historical_place`

---

## Step-by-Step Workflow

### Step 1: Read Each Bibliographic Entry

```
DAVIDSON, HERBERT. Moses Maimonides, The Man and His Works. Oxford: Oxford University Press, 2004.
```

### Step 2: Identify Entities

- **Person**: "Moses Maimonides" (in title)
- **Work**: None explicitly mentioned
- **Place**: "Oxford" (publication place)

### Step 3: Search Wikidata

- Moses Maimonides → Q127398
  - Birth: 1138, Cordoba (Q5818)
  - Death: 1204, Cairo (Q85)
- Oxford → Q34217
  - Coordinates: 51.7520,-1.2577

### Step 4: Create CSV Rows

**persons_extracted.csv:**
```csv
Moses Maimonides,Q127398,1138,1204,Q5818,Q85
```

**places_extracted.csv:**
```csv
Oxford,Q34217,"51.7520,-1.2577",publication_place
```

---

## Example Complete Extraction

### Input:
```
LOBEL, DIANA. Ittisal and the Amr Ilahi: Divine Immanence and the World to Come in the Kuzari. 2006.
```

### Extract:

**Person**: None (no person mentioned in title)

**Work**: "the Kuzari"
- Search Wikidata → Q944985
- Author: Judah Halevi → Q239268
- Language: Arabic

**Place**: None (no publication place given)

### Output:

**works_extracted.csv:**
```csv
The Kuzari,Judah Halevi,Arabic,Q944985
```

**persons_extracted.csv:**
```csv
Judah Halevi,Q239268,1075,1141,Q5836,Q1218
```

---

## Wikidata Integration (CRITICAL)

### How to Search Wikidata:

**Method 1: Web Search**
1. Go to https://www.wikidata.org
2. Search for entity name
3. Copy QID from URL

**Method 2: API**
```bash
curl "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=Maimonides&language=en&format=json"
```

### How to Get Coordinates:

1. Go to Wikidata page (e.g., https://www.wikidata.org/wiki/Q34217)
2. Find "coordinate location" (P625)
3. Copy latitude and longitude
4. Format as `"51.7520,-1.2577"` (with quotes!)

### How to Get Birth/Death Data:

From Wikidata entity:
- P19 = place of birth → Get QID
- P20 = place of death → Get QID
- P569 = date of birth → Extract year
- P570 = date of death → Extract year

---

## Validation Checklist

Before submitting your CSVs:

- [ ] All persons have names
- [ ] All works have titles
- [ ] **ALL places have Wikidata QIDs**
- [ ] **ALL places have coordinates in "lat,lon" format with quotes**
- [ ] No duplicate names within each file
- [ ] UTF-8 encoding
- [ ] Header rows present
- [ ] No trailing commas

---

## Common Patterns to Recognize

### Person Name Patterns:
- `[Name]'s [Topic]` → Extract [Name]
- `[Name], The Man and His Works` → Extract [Name]
- `[Name] and [Name2]` → Extract both
- `([Alternative Name])` → Extract both names

### Work Title Patterns:
- Italicized titles
- Titles in quotes
- Well-known medieval works
- Usually capitalized

### Place Patterns:
- `[City]: [Publisher]` → Extract [City]
- Geographic names in titles
- Historical location references

---

## Expected Output

You should produce **3 CSV files**:

1. **persons_extracted.csv** - All historical persons mentioned
2. **works_extracted.csv** - All historical works mentioned
3. **places_extracted.csv** - All places (publication + historical)

**Quality targets:**
- Extract 80%+ of persons mentioned in titles
- Extract 90%+ of historical works mentioned
- Extract 100% of publication places
- 100% of places must have coordinates and Wikidata QIDs

---

## Questions?

If you encounter:
- **Ambiguous names**: Search Wikidata, use most likely match
- **Multiple people with same name**: Use context to determine which one
- **Unknown works**: Leave optional fields empty, but include the work
- **Places without Wikidata**: Skip that place (don't include without QID)

**Good luck with extraction!** 🚀
