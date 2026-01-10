#!/usr/bin/env python3
"""
bring2knuspr - Fetch shopping list from Bring! and search on Knuspr.
"""

import argparse
import asyncio
import os
import sys
import webbrowser
from urllib.parse import quote

import aiohttp
from bring_api import Bring
from dotenv import load_dotenv


KNUSPR_SEARCH_URL = "https://www.knuspr.de/suche?q={query}&companyId=1"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch shopping list from Bring! and search on Knuspr."
    )
    parser.add_argument("-e", "--email", help="Bring! account email")
    parser.add_argument("-p", "--password", help="Bring! account password")
    parser.add_argument("-l", "--list", dest="list_name", help="List name or UUID")
    parser.add_argument(
        "-s", "--separate", action="store_true", help="Search items individually"
    )
    parser.add_argument(
        "-d", "--dry-run", action="store_true", help="Print URLs without opening browser"
    )
    parser.add_argument(
        "--env-file", default=".env", help="Path to .env file (default: .env)"
    )
    return parser.parse_args()


def load_credentials(args):
    """Load credentials with priority: CLI > env > .env file."""
    if os.path.exists(args.env_file):
        load_dotenv(args.env_file)

    email = args.email or os.getenv("BRING_EMAIL")
    password = args.password or os.getenv("BRING_PASSWORD")
    list_name = args.list_name or os.getenv("BRING_LIST")

    if not email or not password:
        print("Error: Missing credentials.", file=sys.stderr)
        print("Provide via --email/--password, environment variables, or .env file.", file=sys.stderr)
        sys.exit(1)

    return email, password, list_name


def generate_knuspr_urls(items: list[str], separate: bool) -> list[str]:
    """Generate Knuspr search URL(s) for the given items."""
    if separate:
        return [KNUSPR_SEARCH_URL.format(query=quote(item)) for item in items]
    else:
        combined = ", ".join(items)
        return [KNUSPR_SEARCH_URL.format(query=quote(combined))]


def prompt_yes_no(message: str, default: bool = True) -> bool:
    """Prompt user for yes/no confirmation."""
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        response = input(f"{message} {suffix}: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False

    if not response:
        return default
    return response in ("y", "yes")


def prompt_search_mode(item_count: int) -> bool:
    """Prompt user for search mode. Returns True for separate searches."""
    print(f"\nSearch all {item_count} items together or separately?")
    print("(Separate searches give better results but open multiple browser tabs)")
    try:
        response = input("[T/s]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False

    return response == "s"


async def select_list(bring: Bring, list_name: str | None):
    """Select a shopping list, interactively if needed."""
    lists_response = await bring.load_lists()
    lists = lists_response.lists

    if not lists:
        print("Error: No shopping lists found.", file=sys.stderr)
        return None

    if list_name:
        for lst in lists:
            if lst.name.lower() == list_name.lower() or lst.listUuid == list_name:
                return lst
        print(f"Error: List '{list_name}' not found.", file=sys.stderr)
        print("Available lists:", file=sys.stderr)
        for lst in lists:
            print(f"  - {lst.name}", file=sys.stderr)
        return None

    if len(lists) == 1:
        return lists[0]

    print("Available lists:")
    for i, lst in enumerate(lists, 1):
        print(f"  {i}) {lst.name}")

    try:
        choice = input(f"Select list [1-{len(lists)}]: ").strip()
        index = int(choice) - 1
        if 0 <= index < len(lists):
            return lists[index]
    except (ValueError, EOFError, KeyboardInterrupt):
        pass

    print("Invalid selection.", file=sys.stderr)
    return None


async def main():
    args = parse_args()
    email, password, list_name = load_credentials(args)

    async with aiohttp.ClientSession() as session:
        bring = Bring(session, email, password)

        try:
            await bring.login()
        except Exception as e:
            print(f"Error: Login failed - {e}", file=sys.stderr)
            sys.exit(1)

        selected_list = await select_list(bring, list_name)
        if not selected_list:
            sys.exit(1)

        list_uuid = selected_list.listUuid
        list_response = await bring.get_list(list_uuid)

        purchase_items = list_response.items.purchase
        if not purchase_items:
            print(f"No active items in list '{selected_list.name}'.")
            sys.exit(0)

        item_names = [item.itemId for item in purchase_items]

        print(f"Found {len(item_names)} items:\n{', '.join(item_names)}")

        if args.separate:
            separate = True
        elif args.dry_run or len(item_names) <= 3:
            separate = False
        else:
            separate = prompt_search_mode(len(item_names))

        urls = generate_knuspr_urls(item_names, separate)

        print("\nKnuspr search URL(s):")
        for url in urls:
            print(f"  {url}")

        if not args.dry_run:
            if prompt_yes_no("\nOpen in browser?", default=True):
                for url in urls:
                    webbrowser.open(url)


if __name__ == "__main__":
    asyncio.run(main())
