# bring2knuspr

Fetch shopping list items from [Bring!](https://www.getbring.com/) and search them on [Knuspr](https://www.knuspr.de/).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with your Bring! credentials:

```
BRING_EMAIL=your@email.com
BRING_PASSWORD=yourpassword
BRING_LIST=Optional List Name
BRING_MARK_BOUGHT=ask  # auto, skip, or ask (default)
```

## Item Mappings

Map Bring! item names to specific Knuspr search terms via `knuspr_mappings.txt`. The file uses a simple `item name = search term` format, one mapping per line. Lines starting with `#` are comments, empty lines are ignored. Matching is case-insensitive on the item name. Only the first mapping for a given item name is used. The item specification from Bring! (e.g. "1L") is still appended to the mapped search term automatically.

```
# My preferred brands
Oat Milk = Alpro Not Milk Barista
Muesli = Bergsteiger Müsli
```

Mapped items show the mapping in the item list:

```
Oat Milk (1L) → Alpro Not Milk Barista [🔥 urgent]
```

Configure the mapping file path via `--mappings`, `KNUSPR_MAPPINGS` env var, or the default `knuspr_mappings.txt`.

## Usage

```bash
# Interactive mode
python bring2knuspr.py

# Specify list via CLI
python bring2knuspr.py -l "Shopping"

# Search items separately
python bring2knuspr.py --separate

# Dry run (print URLs without opening browser)
python bring2knuspr.py --dry-run
```

## Options

| Argument | Short | Description |
| :--- | :--- | :--- |
| `--email` | `-e` | Bring! account email |
| `--password` | `-p` | Bring! account password |
| `--list` | `-l` | List name or UUID |
| `--separate` | `-s` | Search items individually |
| `--dry-run` | `-d` | Print URLs without opening browser |
| `--mark` | `-m` | Auto-mark items as bought in Bring! |
| `--no-mark` | - | Skip marking items as bought |
| `--env-file` | - | Path to .env file (default: `.env`) |
| `--mappings` | - | Path to item mapping file (default: `knuspr_mappings.txt`) |
