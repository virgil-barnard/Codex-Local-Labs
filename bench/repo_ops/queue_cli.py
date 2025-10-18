"""Command line helpers for managing the human feedback queue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .queue import (
    DEFAULT_LEDGER_PATH,
    DEFAULT_QUEUE_PATH,
    add_request,
    load_queue,
    reconcile_queue,
)


def _cmd_add(args: argparse.Namespace) -> int:
    entry = add_request(
        suite=args.suite,
        profile=args.profile,
        notes=args.notes,
        request_id=args.id,
        priority=args.priority,
        queue_path=args.queue,
    )
    print(json.dumps(entry, indent=2, sort_keys=True))
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    queue = load_queue(args.queue)
    if not queue:
        print("[]")
        return 0
    print(json.dumps(queue, indent=2, sort_keys=True))
    return 0


def _cmd_reconcile(args: argparse.Namespace) -> int:
    updated = reconcile_queue(queue_path=args.queue, ledger_path=args.ledger)
    print(f"Reconciled {updated} queue entries")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Append a new request to the queue")
    add_parser.add_argument("--suite", required=True, help="Benchmark suite name")
    add_parser.add_argument("--profile", required=True, help="Codex profile to use")
    add_parser.add_argument("--notes", default=None, help="Optional free-form notes")
    add_parser.add_argument("--id", help="Optional request id (defaults to timestamp-based id)")
    add_parser.add_argument("--priority", type=int, default=None, help="Optional priority marker")
    add_parser.add_argument(
        "--queue",
        type=Path,
        default=DEFAULT_QUEUE_PATH,
        help=f"Path to queue file (default: {DEFAULT_QUEUE_PATH})",
    )
    add_parser.set_defaults(func=_cmd_add)

    list_parser = subparsers.add_parser("list", help="Print the current queue as JSON")
    list_parser.add_argument(
        "--queue",
        type=Path,
        default=DEFAULT_QUEUE_PATH,
        help=f"Path to queue file (default: {DEFAULT_QUEUE_PATH})",
    )
    list_parser.set_defaults(func=_cmd_list)

    reconcile_parser = subparsers.add_parser("reconcile", help="Reconcile queue with ledger entries")
    reconcile_parser.add_argument(
        "--queue",
        type=Path,
        default=DEFAULT_QUEUE_PATH,
        help=f"Path to queue file (default: {DEFAULT_QUEUE_PATH})",
    )
    reconcile_parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER_PATH,
        help=f"Path to ledger file (default: {DEFAULT_LEDGER_PATH})",
    )
    reconcile_parser.set_defaults(func=_cmd_reconcile)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
