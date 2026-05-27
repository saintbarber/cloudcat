import argparse
import os

from dotenv import load_dotenv

from cloudcat.config import load_config
from cloudcat.providers import PROVIDER_NAMES, get_provider
from cloudcat.utils import estimated_cost, format_table, format_uptime


def cmd_list(args: argparse.Namespace) -> None:
    config = load_config()
    provider = get_provider(args.provider, config)

    label_prefix = None if args.all else "cc-"
    instances = provider.list_instances(label_prefix=label_prefix)

    if not instances:
        if args.all:
            print("No instances found.")
        else:
            print(
                "No cloudcat instances found. "
                "Use --all to show all vast.ai instances."
            )
        return

    rows: list[list[str]] = []
    for inst in instances:
        label = inst.get("label") or "-"
        instance_id = str(inst.get("id", "-"))
        gpu = inst.get("gpu_name") or "-"
        status = inst.get("actual_status") or "-"
        dph = inst.get("dph_total")
        dph_str = f"${float(dph):.3f}" if dph is not None else "-"
        start = inst.get("start_date")
        uptime = format_uptime(start)
        cost_str = f"${estimated_cost(dph, start):.2f}"
        rows.append([label, instance_id, gpu, status, dph_str, uptime, cost_str])

    headers = ["Label", "Instance ID", "GPU Name", "Status", "$/hr", "Uptime", "Est. Cost"]
    print(format_table(headers, rows))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cloudcat",
        description="Provider-agnostic CLI for managing cloud GPU instances for hashcat",
    )

    # Provider selection with default from env var or "vastai"

    parser.add_argument(
        "--provider",
        choices=PROVIDER_NAMES,
        default=os.environ.get("CLOUDCAT_PROVIDER", "vastai"),
        help="Cloud provider to use (default: vastai, or $CLOUDCAT_PROVIDER)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List command - lists all isntances created by cloudcat (those with label starting with "cc-"), or all instances if --all is used

    p_list = subparsers.add_parser("list", help="List instances created by cloudcat")
    p_list.add_argument(
        "--all",
        action="store_true",
        help="Show all instances, not just those with the cc- prefix",
    )
    p_list.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
