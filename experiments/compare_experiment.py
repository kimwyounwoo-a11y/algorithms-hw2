"""Compare separate chaining and linear probing across load factors."""

import csv
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.hash_table import HashTable
from src.linear_probing_table import LinearProbingTable

TABLE_SIZE = 4093
FAILURE_SAMPLES = TABLE_SIZE
RANDOM_SEED = 20261126
TARGET_LOAD_FACTORS = tuple(step / 10 for step in range(1, 10))
OUTPUT_DIR = Path(__file__).resolve().parent
CSV_PATH = OUTPUT_DIR / "compare_results.csv"
SVG_PATH = OUTPUT_DIR / "compare_results.svg"


@dataclass(frozen=True)
class Result:
    target_load_factor: float
    load_factor: float
    item_count: int
    chaining_success_measured: float
    chaining_success_theory: float
    chaining_failure_measured: float
    chaining_failure_theory: float
    linear_success_measured: float
    linear_success_theory: float
    linear_failure_measured: float
    linear_failure_theory: float


def _random_urls(rng: random.Random, kind: str, count: int) -> list[str]:
    return [
        f"https://example.com/{kind}/{rng.getrandbits(128):032x}-{index}"
        for index in range(count)
    ]


def run_experiment() -> list[Result]:
    rng = random.Random(RANDOM_SEED)
    max_items = round(TARGET_LOAD_FACTORS[-1] * TABLE_SIZE)
    all_keys = _random_urls(rng, "stored", max_items)
    misses = _random_urls(rng, "missing", FAILURE_SAMPLES)
    results = []

    for target_load_factor in TARGET_LOAD_FACTORS:
        item_count = round(target_load_factor * TABLE_SIZE)
        keys = all_keys[:item_count]
        chaining = HashTable(capacity=TABLE_SIZE, max_load=None)
        linear = LinearProbingTable(capacity=TABLE_SIZE, max_load=None)

        for index, key in enumerate(keys):
            chaining.put(key, index)
            linear.put(key, index)

        if chaining.capacity != TABLE_SIZE or linear.capacity != TABLE_SIZE:
            raise RuntimeError("A comparison table changed its fixed capacity")

        alpha = item_count / TABLE_SIZE
        chaining_success = sum(chaining.probe_count(key) for key in keys) / item_count
        chaining_failure = (
            sum(chaining.probe_count(key) for key in misses) / len(misses)
        )
        linear_success = sum(linear.probe_count(key) for key in keys) / item_count
        linear_failure = sum(linear.probe_count(key) for key in misses) / len(misses)

        results.append(
            Result(
                target_load_factor=target_load_factor,
                load_factor=alpha,
                item_count=item_count,
                chaining_success_measured=chaining_success,
                chaining_success_theory=1 + alpha / 2,
                chaining_failure_measured=chaining_failure,
                chaining_failure_theory=alpha,
                linear_success_measured=linear_success,
                linear_success_theory=(1 + 1 / (1 - alpha)) / 2,
                linear_failure_measured=linear_failure,
                linear_failure_theory=(1 + 1 / (1 - alpha) ** 2) / 2,
            )
        )

    return results


def write_csv(results: list[Result]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            (
                "target_load_factor",
                "load_factor",
                "item_count",
                "chaining_success_measured",
                "chaining_success_theory",
                "chaining_failure_measured",
                "chaining_failure_theory",
                "linear_success_measured",
                "linear_success_theory",
                "linear_failure_measured",
                "linear_failure_theory",
            )
        )
        for result in results:
            writer.writerow(
                (
                    f"{result.target_load_factor:.1f}",
                    f"{result.load_factor:.6f}",
                    result.item_count,
                    f"{result.chaining_success_measured:.6f}",
                    f"{result.chaining_success_theory:.6f}",
                    f"{result.chaining_failure_measured:.6f}",
                    f"{result.chaining_failure_theory:.6f}",
                    f"{result.linear_success_measured:.6f}",
                    f"{result.linear_success_theory:.6f}",
                    f"{result.linear_failure_measured:.6f}",
                    f"{result.linear_failure_theory:.6f}",
                )
            )


def write_svg(results: list[Result]) -> None:
    width, height = 1120, 680
    left, right, top, bottom = 88, 34, 132, 72
    plot_width = width - left - right
    plot_height = height - top - bottom
    min_load = results[0].load_factor
    max_load = results[-1].load_factor
    max_value = max(
        result.linear_failure_theory for result in results
    )
    max_value = max(
        max_value,
        max(result.linear_failure_measured for result in results),
        max(result.linear_success_measured for result in results),
    )
    y_max = math.ceil(max_value * 1.08)

    def x_position(load_factor: float) -> float:
        return left + (load_factor - min_load) / (max_load - min_load) * plot_width

    def y_position(value: float) -> float:
        return top + (y_max - value) / y_max * plot_height

    series = (
        (
            "Chaining success measured",
            "#1d4ed8",
            False,
            [result.chaining_success_measured for result in results],
        ),
        (
            "Chaining success theory",
            "#1d4ed8",
            True,
            [result.chaining_success_theory for result in results],
        ),
        (
            "Chaining failure measured",
            "#0284c7",
            False,
            [result.chaining_failure_measured for result in results],
        ),
        (
            "Chaining failure theory",
            "#0284c7",
            True,
            [result.chaining_failure_theory for result in results],
        ),
        (
            "Linear success measured",
            "#b91c1c",
            False,
            [result.linear_success_measured for result in results],
        ),
        (
            "Linear success theory",
            "#b91c1c",
            True,
            [result.linear_success_theory for result in results],
        ),
        (
            "Linear failure measured",
            "#ea580c",
            False,
            [result.linear_failure_measured for result in results],
        ),
        (
            "Linear failure theory",
            "#ea580c",
            True,
            [result.linear_failure_theory for result in results],
        ),
    )

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>Hash table probe counts by load factor</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2:.0f}" y="30" text-anchor="middle" font-family="sans-serif" font-size="20">Chaining vs. Linear Probing</text>',
    ]

    for series_index, (label, color, dashed, _) in enumerate(series):
        legend_column = series_index % 4
        legend_row = series_index // 4
        legend_x = left + legend_column * 250
        legend_y = 58 + legend_row * 22
        dash_attribute = ' stroke-dasharray="7 5"' if dashed else ""
        lines.extend(
            (
                f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 28}" y2="{legend_y}" stroke="{color}" stroke-width="2.5"{dash_attribute}/>',
                f'<text x="{legend_x + 36}" y="{legend_y + 4}" font-family="sans-serif" font-size="11">{label}</text>',
            )
        )

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
                f'<text x="{x:.2f}" y="{top + plot_height + 22}" text-anchor="middle" font-family="sans-serif" font-size="11">{result.target_load_factor:.1f}</text>',
            )
        )

    lines.extend(
        (
            f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#111827"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#111827"/>',
            f'<text x="{left + plot_width / 2:.2f}" y="{height - 20}" text-anchor="middle" font-family="sans-serif" font-size="14">Target load factor</text>',
            f'<text x="20" y="{top + plot_height / 2:.2f}" text-anchor="middle" transform="rotate(-90 20 {top + plot_height / 2:.2f})" font-family="sans-serif" font-size="14">Average probes / nodes</text>',
        )
    )

    for _, color, dashed, values in series:
        points = " ".join(
            f"{x_position(result.load_factor):.2f},{y_position(value):.2f}"
            for result, value in zip(results, values)
        )
        dash_attribute = ' stroke-dasharray="7 5"' if dashed else ""
        lines.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.2"{dash_attribute}/>'
        )
        for result, value in zip(results, values):
            lines.append(
                f'<circle cx="{x_position(result.load_factor):.2f}" cy="{y_position(value):.2f}" r="3" fill="{color}"/>'
            )

    lines.append("</svg>")
    SVG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_table(results: list[Result]) -> None:
    print(
        f"{'target':>6} {'actual α':>9} {'n':>5}"
        f" {'chain S':>9} {'theory':>8} {'chain F':>9} {'theory':>8}"
        f" {'linear S':>9} {'theory':>8} {'linear F':>9} {'theory':>8}"
    )
    for result in results:
        print(
            f"{result.target_load_factor:6.1f} {result.load_factor:9.4f}"
            f" {result.item_count:5d}"
            f" {result.chaining_success_measured:9.3f} {result.chaining_success_theory:8.3f}"
            f" {result.chaining_failure_measured:9.3f} {result.chaining_failure_theory:8.3f}"
            f" {result.linear_success_measured:9.3f} {result.linear_success_theory:8.3f}"
            f" {result.linear_failure_measured:9.3f} {result.linear_failure_theory:8.3f}"
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
