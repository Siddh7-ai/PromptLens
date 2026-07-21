import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.compress.json_compressor import compress_json
from src.compress.text_compressor import compress_text

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def main():
    fixtures = sorted([
        f for f in os.listdir(FIXTURES_DIR)
        if os.path.isfile(os.path.join(FIXTURES_DIR, f)) and not f.startswith("compressed_")
    ])

    header_fmt = "| {:<28} | {:>12} | {:>12} | {:>12} |"
    divider = "-" * 73
    print(divider)
    print(header_fmt.format("Fixture File", "Original", "Compressed", "Savings"))
    print(divider)

    total_orig = 0
    total_comp = 0

    for name in fixtures:
        path = os.path.join(FIXTURES_DIR, name)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if name.endswith(".json"):
            res = compress_json(content, max_array_items=3)
        else:
            res = compress_text(content, head_lines=5, tail_lines=5)

        total_orig += res.original_tokens
        total_comp += res.compressed_tokens
        savings_pct = f"{res.compression_ratio * 100:.2f}%"

        print(header_fmt.format(name, res.original_tokens, res.compressed_tokens, savings_pct))

    print(divider)
    total_savings = f"{(1.0 - (total_comp / total_orig)) * 100:.2f}%"
    print(header_fmt.format("TOTAL", total_orig, total_comp, total_savings))
    print(divider)

if __name__ == "__main__":
    main()
