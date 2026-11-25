"""Compare separate-chaining probe counts with textbook load-factor estimates."""

import csv
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.hash_table import HashTable

TABLE_SIZE = 4093
UNSUCCESSFUL_SAMPLES = TABLE_SIZE
RANDOM_SEED = 20261125
LOAD_FACTORS = tuple(step / 4 for step in range(1, 17))
OUTPUT_DIR = Path(__file__).resolve().parent
CSV_PATH = OUTPUT_DIR / "results.csv"
SVG_PATH = OUTPUT_DIR / "results.svg"


@dataclass(frozen=True)
class Result:
    load_factor: float
    item_count: int
    successful_measured: float
    successful_theory: float
    unsuccessful_measured: float
    unsuccessful_theory: float


def _random_urls(rng: random.Random, kind: str, count: int) -> list[str]:
    return [
        f"https://example.com/{kind}/{rng.getrandbits(128):032x}-{index}"
        for index in range(count)
    ]


def run_experiment() -> list[Result]:
    rng = random.Random(RANDOM_SEED)
    results = []

    for target_load in LOAD_FACTORS:
        item_count = round(target_load * TABLE_SIZE)
        urls = _random_urls(rng, "stored", item_count)
        table = HashTable(capacity=TABLE_SIZE, max_load=None)
        for index, url in enumerate(urls):
            table.put(url, index)

        if table.capacity != TABLE_SIZE:
            raise RuntimeError("The fixed-size hash table unexpectedly resized")

        misses = _random_urls(rng, "missing", UNSUCCESSFUL_SAMPLES)
        alpha = len(urls) / table.capacity
        successful_measured = sum(table.probe_count(url) for url in urls) / len(urls)
        unsuccessful_measured = (
            sum(table.probe_count(url) for url in misses) / len(misses)
        )
        results.append(
            Result(
                load_factor=alpha,
                item_count=len(urls),
                successful_measured=successful_measured,
                successful_theory=1 + alpha / 2,
                unsuccessful_measured=unsuccessful_measured,
                unsuccessful_theory=alpha,
            )
        )

    return results


def write_csv(results: list[Result]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            (
                "load_factor",
                "item_count",
                "successful_measured",
                "successful_theory",
                "unsuccessful_measured",
                "unsuccessful_theory",
            )
        )
        for result in results:
            writer.writerow(
                (
                    f"{result.load_factor:.6f}",
                    result.item_count,
                    f"{result.successful_measured:.6f}",
                    f"{result.successful_theory:.6f}",
                    f"{result.unsuccessful_measured:.6f}",
                    f"{result.unsuccessful_theory:.6f}",
                )
            )


def write_svg(results: list[Result]) -> None:
    width, height = 960, 600
    left, right, top, bottom = 82, 30, 82, 68
    plot_width = width - left - right
    plot_height = height - top - bottom
    min_load = results[0].load_factor
    max_load = results[-1].load_factor
    max_value = max(
        result.successful_measured for result in results
    )
    max_value = max(
        max_value,
        max(result.unsuccessful_measured for result in results),
        max(result.successful_theory for result in results),
        max(result.unsuccessful_theory for result in results),
    )
    y_max = math.ceil(max_value * 1.15)

    def x_position(load_factor: float) -> float:
        return left + (load_factor - min_load) / (max_load - min_load) * plot_width

    def y_position(value: float) -> float:
        return top + (y_max - value) / y_max * plot_height

    series = (
        (
            "Success measured",
            "#2563eb",
            False,
            [result.successful_measured for result in results],
        ),
        (
            "Success theory: 1 + alpha/2",
            "#2563eb",
            True,
            [result.successful_theory for result in results],
        ),
        (
            "Failure measured",
            "#dc2626",
            False,
            [result.unsuccessful_measured for result in results],
        ),
        (
            "Failure theory: alpha",
            "#dc2626",
            True,
            [result.unsuccessful_theory for result in results],
        ),
    )

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>Hash table probe counts by load factor</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="480" y="30" text-anchor="middle" font-family="sans-serif" font-size="20">Probe counts by load factor</text>',
    ]

    for tick in range(y_max + 1):
        y = y_position(tick)
        lines.extend(
            (
                f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#e5e7eb"/>',
                f'<text x="{left - 12}" y="{y + 5:.2f}" text-anchor="end" font-family="sans-serif" font-size="12">{tick}</text>',
            )
        )

    for result in results:
        x = x_position(result.load_factor)
        lines.extend(
            (
                f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_height}" stroke="#f3f4f6"/>',
                f'<text x="{x:.2f}" y="{top + plot_height + 22}" text-anchor="middle" font-family="sans-serif" font-size="10">{result.load_factor:.2f}</text>',
            )
        )

    lines.extend(
        (
            f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#111827"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#111827"/>',
            f'<text x="{left + plot_width / 2:.2f}" y="{height - 18}" text-anchor="middle" font-family="sans-serif" font-size="14">Load factor (alpha)</text>',
            f'<text x="20" y="{top + plot_height / 2:.2f}" text-anchor="middle" transform="rotate(-90 20 {top + plot_height / 2:.2f})" font-family="sans-serif" font-size="14">Mean nodes compared</text>',
        )
    )

    for series_index, (label, color, dashed, values) in enumerate(series):
        points = " ".join(
            f"{x_position(result.load_factor):.2f},{y_position(value):.2f}"
            for result, value in zip(results, values)
        )
        dash_attribute = ' stroke-dasharray="7 5"' if dashed else ""
        lines.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.5"{dash_attribute}/>'
        )
        for result, value in zip(results, values):
            lines.append(
                f'<circle cx="{x_position(result.load_factor):.2f}" cy="{y_position(value):.2f}" r="2.5" fill="{color}"/>'
            )
        legend_x = left + (series_index % 2) * 410
        legend_y = 52 + (series_index // 2) * 18
        lines.extend(
            (
                f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 28}" y2="{legend_y}" stroke="{color}" stroke-width="2.5"{dash_attribute}/>',
                f'<text x="{legend_x + 36}" y="{legend_y + 4}" font-family="sans-serif" font-size="12">{label}</text>',
            )
        )

    lines.append("</svg>")
    SVG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_table(results: list[Result]) -> None:
    print(
        f"{'alpha':>8} {'n':>7} {'success avg':>13} {'success theory':>15}"
        f" {'failure avg':>13} {'failure theory':>15}"
    )
    for result in results:
        print(
            f"{result.load_factor:8.3f} {result.item_count:7d}"
            f" {result.successful_measured:13.4f} {result.successful_theory:15.4f}"
            f" {result.unsuccessful_measured:13.4f} {result.unsuccessful_theory:15.4f}"
        )


def main() -> None:
    results = run_experiment()
    write_csv(results)
    write_svg(results)
    print_table(results)
    print(f"\nCSV: {CSV_PATH}")
    print(f"SVG: {SVG_PATH}")


if __name__ == "__main__":
    main()
