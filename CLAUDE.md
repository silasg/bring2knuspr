# bring2knuspr

Single-file Python script to fetch Bring! shopping list items and search on Knuspr.

## Tech Stack

- Python 3.8+
- `bring-api` - Unofficial Bring! API client (async)
- `python-dotenv` - Environment file loading
- `aiohttp` - Async HTTP client

## Project Structure

```
bring2knuspr.py        # Main script (single file)
requirements.txt       # Python dependencies
.env                   # Credentials (not in git)
knuspr_mappings.txt    # Item name → search term mappings (not in git)
```

## Development

```bash
source venv/bin/activate
python bring2knuspr.py --dry-run
```

## Notes

- The `bring-api` library returns typed dataclass objects, not dicts
- Use `.lists`, `.items.purchase`, `.itemId` etc. for attribute access
- Active items are in `items.purchase`, completed items in `items.recently`
