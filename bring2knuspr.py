#!/usr/bin/env python3
"""
bring2knuspr - Fetch shopping list from Bring! and search on Knuspr.
"""

import argparse
import asyncio
import os
import sys
import termios
import tty
import webbrowser
from urllib.parse import quote

import aiohttp
from bring_api import Bring
from dotenv import load_dotenv


KNUSPR_SEARCH_URL = "https://www.knuspr.de/suche?q={query}&companyId=1"


def format_item_for_search(item) -> str:
    """Format item name with specification for search queries."""
    if item.specification:
        return f"{item.itemId} ({item.specification})"
    return item.itemId


def format_attributes(item) -> str:
    """Format item attributes as emoji labels."""
    labels = []
    for attr in item.attributes:
        if attr.content.urgent:
            labels.append("🔥 urgent")
        if attr.content.discounted:
            labels.append("💰 on sale")
        if attr.content.convenient:
            labels.append("🍀 convenient")
    return f" [{', '.join(labels)}]" if labels else ""


def format_item_for_display(item) -> str:
    """Format item name with specification and attributes for display."""
    name = item.itemId
    if item.specification:
        name = f"{name} ({item.specification})"
    name += format_attributes(item)
    return name


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
    mark_group = parser.add_mutually_exclusive_group()
    mark_group.add_argument(
        "-m", "--mark", action="store_true", help="Auto-mark items as bought in Bring!"
    )
    mark_group.add_argument(
        "--no-mark", action="store_true", help="Skip marking items as bought"
    )
    return parser.parse_args()


def load_config(args):
    """Load config with priority: CLI > env > .env file."""
    if os.path.exists(args.env_file):
        load_dotenv(args.env_file)

    email = args.email or os.getenv("BRING_EMAIL")
    password = args.password or os.getenv("BRING_PASSWORD")
    list_name = args.list_name or os.getenv("BRING_LIST")

    if not email or not password:
        print("Error: Missing credentials.", file=sys.stderr)
        print("Provide via --email/--password, environment variables, or .env file.", file=sys.stderr)
        sys.exit(1)

    # Determine mark behavior: CLI flags take precedence over env
    if args.mark:
        mark_bought = "auto"
    elif args.no_mark:
        mark_bought = "skip"
    else:
        mark_bought = os.getenv("BRING_MARK_BOUGHT", "ask").lower()
        if mark_bought not in ("auto", "skip", "ask"):
            mark_bought = "ask"

    return email, password, list_name, mark_bought


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


def read_key() -> str:
    """Read a single keypress from stdin in raw mode."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = sys.stdin.read(1)
            if seq == "[":
                code = sys.stdin.read(1)
                if code == "A":
                    return "up"
                if code == "B":
                    return "down"
            return "esc"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def interactive_mark_checklist(display_names: list[str]) -> list[int] | None:
    """Show interactive checklist. Returns selected indices or None on cancel."""
    checked = [True] * len(display_names)
    cursor = 0
    total = len(display_names)
    header = "Mark items as bought in Bring!:\n"
    footer = (
        "\n  j/↓ down  k/↑ up  space toggle  a all  n none  i invert"
        "\n  enter confirm  q/esc cancel"
    )
    # total lines = 1 (header) + total items + 1 (blank) + 2 (footer)
    output_lines = 1 + total + 1 + 2

    def render(first: bool = False):
        if not first:
            sys.stdout.write(f"\x1b[{output_lines}A")
        sys.stdout.write(header)
        for idx, name in enumerate(display_names):
            mark = "x" if checked[idx] else " "
            arrow = ">" if idx == cursor else " "
            sys.stdout.write(f"\x1b[2K  {arrow} [{mark}] {name}\n")
        sys.stdout.write(f"\x1b[2K{footer}\n")
        sys.stdout.flush()

    render(first=True)

    while True:
        key = read_key()

        if key in ("q", "esc", "\x03"):  # q, Esc, Ctrl-C
            return None
        elif key in ("\r", "\n"):  # Enter
            return [i for i, c in enumerate(checked) if c]
        elif key in ("j", "down"):
            cursor = min(cursor + 1, total - 1)
        elif key in ("k", "up"):
            cursor = max(cursor - 1, 0)
        elif key == " ":
            checked[cursor] = not checked[cursor]
        elif key == "a":
            checked = [True] * total
        elif key == "n":
            checked = [False] * total
        elif key == "i":
            checked = [not c for c in checked]
        else:
            continue

        render()


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
    email, password, list_name, mark_bought = load_config(args)

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

        display_names = [format_item_for_display(item) for item in purchase_items]
        search_names = [format_item_for_search(item) for item in purchase_items]

        print(f"Found {len(display_names)} items:\n{', '.join(display_names)}")

        if args.separate:
            separate = True
        elif args.dry_run or len(display_names) <= 1:
            separate = False
        else:
            separate = prompt_search_mode(len(display_names))

        urls = generate_knuspr_urls(search_names, separate)

        print("\nKnuspr search URL(s):")
        for url in urls:
            print(f"  {url}")

        if not args.dry_run:
            if prompt_yes_no("\nOpen in browser?", default=True):
                for url in urls:
                    webbrowser.open(url)

            if mark_bought == "auto":
                items_to_mark = list(range(len(purchase_items)))
            elif mark_bought == "ask":
                print()
                items_to_mark = interactive_mark_checklist(display_names)
            else:
                items_to_mark = None

            if items_to_mark is None:
                print("Skipped marking items.")
            elif items_to_mark:
                total = len(items_to_mark)
                for i, idx in enumerate(items_to_mark, 1):
                    item = purchase_items[idx]
                    print(f"\rMarking items as bought: {i}/{total}", end="", flush=True)
                    await bring.complete_item(list_uuid, item.itemId)
                print(f"\rMarked {total} item(s) as bought.        ")
            else:
                print("No items selected.")


if __name__ == "__main__":
    asyncio.run(main())
