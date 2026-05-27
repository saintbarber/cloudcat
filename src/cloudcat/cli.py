import argparse
import os

from dotenv import load_dotenv

from cloudcat.config import load_config
from cloudcat.providers import PROVIDER_NAMES, get_provider
from cloudcat.utils import estimated_cost, format_table, format_uptime

# GPU families - vast.ai gpu_name values grouped by hashcat-relevant generations.
# These names may need adjustment if vast.ai changes their naming.
GPU_FAMILIES: dict[str, list[str]] = {
    "rtx-50": ["RTX_5090", "RTX_5080", "RTX_5070_Ti", "RTX_5070", "RTX_5060_Ti", "RTX_5060"],
    "rtx-40": ["RTX_4090", "RTX_4080S", "RTX_4080", "RTX_4070S_Ti", "RTX_4070_Ti","RTX_4070S", "RTX_4070", "RTX_4060_Ti", "RTX_4060"],
    "rtx-30": ["RTX_3090_Ti", "RTX_3090", "RTX_3080_Ti", "RTX_3080","RTX_3070_Ti", "RTX_3070","RTX_3060_Ti", "RTX_3060"],
    "hopper": ["H100_SXM", "H100_PCIE", "H100_NVL", "H200"],
    "ampere-dc": ["A100_SXM4", "A100_PCIE", "A100"],
}


def cmd_search(args: argparse.Namespace) -> None:
    config = load_config()
    provider = get_provider(args.provider, config)

    # Default search values have been set
    #   Show only verified
    #   Show only rentable
    #   Show only offers with at least 1 direct port
    #   Show only offers with at least 20GB disk space
    #   Show only offers with reliability >= 0.9

    if args.gpu_family:
        gpu_names = GPU_FAMILIES[args.gpu_family]
    elif args.gpu:
        gpu_names = [args.gpu]
    else:
        gpu_names = None

    offers = provider.search_offers(
        gpu_names=gpu_names,
        num_gpus=args.number,
        limit=args.limit,
    )

    if not offers:
        print("No offers found. Try broadening your filters.")
        return

    rows: list[list[str]] = []
    for o in offers:
        offer_id = str(o.get("machine_id", "-"))
        gpu = o.get("gpu_name") or "-"
        ram_mb = o.get("gpu_ram")
        ram_str = f"{int(ram_mb) // 1024}GB" if ram_mb else "-"
        n = str(o.get("num_gpus", "-"))
        dph = o.get("dph_total")
        dph_str = f"${float(dph):.3f}" if dph is not None else "-"
        debug = str(o.get("gpu_arch")) or "-"
        rows.append([offer_id, gpu, ram_str, n, dph_str, debug])

    headers = ["ID", "GPU Name", "GPU RAM", "Num GPUs", "$/hr", "Debug"]
    print(format_table(headers, rows))


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

    # Search command - lists available GPU offers, optionally filtered by --gpu and --number (1, 2, 4, 8, or 9+), capped by --limit

    p_search = subparsers.add_parser("search", help="Search for available GPU offers")
    gpu_group = p_search.add_mutually_exclusive_group()
    gpu_group.add_argument(
        "--gpu",
        help="Exact GPU model name (e.g. RTX_4090, A100_SXM4)",
    )
    gpu_group.add_argument(
        "--gpu-family",
        choices=list(GPU_FAMILIES),
        help="GPU family filter (e.g. rtx-50, rtx-40, hopper)",
    )
    p_search.add_argument(
        "--number",
        default="1",
        help="Number of GPUs per instance (default: 1)",
    )
    p_search.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of results to show (default: 20)",
    )
    p_search.set_defaults(func=cmd_search)

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
