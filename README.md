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
