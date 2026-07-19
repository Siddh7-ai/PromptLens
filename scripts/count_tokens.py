import os
import tiktoken

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))
ENCODING_NAME = "cl100k_base"

def main():
    try:
        encoding = tiktoken.get_encoding(ENCODING_NAME)
    except Exception as e:
        print(f"Error loading tiktoken encoding {ENCODING_NAME}: {e}")
        return

    if not os.path.exists(FIXTURES_DIR):
        print(f"Fixtures directory not found: {FIXTURES_DIR}")
        return

    fixtures = sorted([f for f in os.listdir(FIXTURES_DIR) if os.path.isfile(os.path.join(FIXTURES_DIR, f))])
    
    if not fixtures:
        print(f"No fixture files found in {FIXTURES_DIR}")
        return

    # Print header
    header_fmt = "| {:<30} | {:>12} | {:>12} |"
    divider = "-" * 62
    print(divider)
    print(header_fmt.format("Fixture File", "Size (Bytes)", "Tokens (cl100k)"))
    print(divider)

    total_bytes = 0
    total_tokens = 0

    for name in fixtures:
        path = os.path.join(FIXTURES_DIR, name)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            size_bytes = os.path.getsize(path)
            tokens = len(encoding.encode(content))
            
            total_bytes += size_bytes
            total_tokens += tokens
            
            print(header_fmt.format(name, size_bytes, tokens))
        except Exception as e:
            print(f"| {name:<30} | ERROR: {str(e)[:24]} |"[:62])

    print(divider)
    print(header_fmt.format("TOTAL", total_bytes, total_tokens))
    print(divider)

if __name__ == "__main__":
    main()
