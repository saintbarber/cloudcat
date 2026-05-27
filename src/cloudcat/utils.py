import secrets
import time


def generate_label() -> str:
    return f"cc-{secrets.token_hex(2)}"


def format_uptime(start_date: float | int | None) -> str:
    if start_date is None:
        return "-"
    seconds = max(0, int(time.time() - float(start_date)))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def estimated_cost(dph: float | None, start_date: float | int | None) -> float:
    if dph is None or start_date is None:
        return 0.0
    hours = max(0.0, (time.time() - float(start_date)) / 3600)
    return float(dph) * hours


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(cells: list[str]) -> str:
        return "  ".join(cell.ljust(w) for cell, w in zip(cells, widths))

    lines = [fmt_row(headers), fmt_row(["-" * w for w in widths])]
    lines.extend(fmt_row(row) for row in rows)
    return "\n".join(lines)
