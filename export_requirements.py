import subprocess
import sys

import shutil


def main() -> int:
    poetry = shutil.which("poetry")
    if poetry is None:
        print("Error: poetry not found")
        return 1
    COMMAMD = [
        poetry,
        "export",
        "--without-hashes",
        "--without-urls",
        "--output=requirements.txt",
    ]
    response = subprocess.run(COMMAMD, check=False, capture_output=True)
    if response.returncode != 0:
        print("failed:")
        print(response.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
