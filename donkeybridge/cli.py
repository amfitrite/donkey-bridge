import argparse
import sys
from donkeybridge.core import DonkeyBridge

def main():
    parser = argparse.ArgumentParser(description="Donkey Bridge CLI")
    parser.add_argument("--db", default="bridges.db", help="Path to the SQLite database")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # INIT
    subparsers.add_parser("init", help="Initialize the database")

    # ADD
    parser_add = subparsers.add_parser("add", help="Add a new bridge")
    parser_add.add_argument("--acronym", required=True, help="The acronym (prompt context)")
    parser_add.add_argument("--peta", required=True, help="The decode map (Stage 1)")
    parser_add.add_argument("--isi", required=True, help="The full payload (Stage 2)")
    parser_add.add_argument("--tags", default="", help="Tags for searching")

    # LIST
    subparsers.add_parser("list", help="Alias for index (returns prompt-friendly index)")
    subparsers.add_parser("index", help="Returns the prompt-friendly index")

    # RECALL
    parser_recall = subparsers.add_parser("recall", help="Recall the map (Stage 1)")
    parser_recall.add_argument("acronym", help="The acronym to recall")

    # OPEN
    parser_open = subparsers.add_parser("open", help="Open the full payload (Stage 2)")
    parser_open.add_argument("id", type=int, help="The DB ID of the bridge")

    # SEARCH
    parser_search = subparsers.add_parser("search", help="Search the database (FTS5)")
    parser_search.add_argument("query", help="The search query")

    # FORGET
    parser_forget = subparsers.add_parser("forget", help="Forget (delete) a bridge")
    parser_forget.add_argument("id", type=int, help="The DB ID of the bridge to delete")

    # STATS
    subparsers.add_parser("stats", help="Show token savings stats")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    db = DonkeyBridge(args.db)

    if args.command == "init":
        print(f"Initialized database at {args.db}")
    elif args.command == "add":
        try:
            db_id = db.add(args.acronym, args.peta, args.isi, args.tags)
            print(f"Added bridge. ID: {db_id}")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
    elif args.command in ("list", "index"):
        idx = db.index()
        if idx:
            print(idx)
        else:
            print("No bridges found.")
    elif args.command == "recall":
        res = db.recall(args.acronym)
        if res:
            print(f"ID: DB-{res['id']}\nMap: {res['peta']}")
        else:
            print(f"Acronym '{args.acronym}' not found.")
            sys.exit(1)
    elif args.command == "open":
        res = db.open(args.id)
        if res:
            print(res)
        else:
            print(f"Bridge ID DB-{args.id} not found.")
            sys.exit(1)
    elif args.command == "search":
        results = db.search(args.query)
        if not results:
            print("No results found.")
        for r in results:
            tags = f" [{r['tags']}]" if r['tags'] else ""
            print(f"DB-{r['rowid']}: {r['acronym']} - {r['peta']}{tags}")
    elif args.command == "forget":
        if db.forget(args.id):
            print(f"Forgot bridge DB-{args.id}.")
        else:
            print(f"Bridge DB-{args.id} not found.")
            sys.exit(1)
    elif args.command == "stats":
        s = db.stats()
        print("=== Donkey Bridge Stats ===")
        print(f"Total Bridges:   {s['total_bridges']}")
        print(f"Context Tokens:  {s['context_tokens_used']}")
        print(f"Payload Tokens:  {s['payload_tokens_on_ssd']}")
        print(f"Tokens Saved:    {s['tokens_saved']} ({s['savings_percent']}%)")

if __name__ == "__main__":
    main()
