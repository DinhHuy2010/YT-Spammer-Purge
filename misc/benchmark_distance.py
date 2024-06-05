"""
Benchmark rapidfuzz and python-Levenshtein time

Author:
    Pushpam Punjabi
    Machine Learning Engineer

modfied by DinhHuy2010
(note removing numpy, re-add numpy if you want)
"""

import datetime as dt
import string

import Levenshtein
import more_itertools as miter
import numpy as np
from rapidfuzz import fuzz


def generate_experiment() -> tuple[list[str], list[str]]:
    CHARS = string.ascii_letters
    minlen = 10
    maxlen = 1000
    NUM_PAIRS = 10000

    # Generate random strings

    def generate_string() -> str:
        # black magic
        # use random module from numpy
        size = np.random.randint(minlen, maxlen)
        return "".join([
            CHARS[idx]
            for idx in np.random.choice(len(CHARS), size=size)
        ])

    # Call generate_string "NUM_PAIRS" times
    # use more-itertools
    x = list(miter.repeatfunc(generate_string, NUM_PAIRS))
    y = list(miter.repeatfunc(generate_string, NUM_PAIRS))

    return x, y


def benchmark_levenshtein(x: list[str], y: list[str]) -> dt.timedelta:
    start = dt.datetime.now()
    for sen_x, sen_y in zip(x, y):
        _ = Levenshtein.ratio(sen_x, sen_y)
    end = dt.datetime.now()
    return end - start

def benchmark_rapidfuzz(x: list[str], y: list[str]) -> dt.timedelta:
    start = dt.datetime.now()
    for sen_x, sen_y in zip(x, y):
        _ = fuzz.ratio(sen_x, sen_y)
    end = dt.datetime.now()
    return end - start

def main() -> None:
    print("Generating experiment...")

    # Create random sentences
    x, y = generate_experiment()

    print("Generated experiment.")
    print("Running benchmark...")

    # Benchmart time for python-Levenshtein
    levenshtein_time = benchmark_levenshtein(x, y)
    print(f"python-Levenshtein time: {levenshtein_time}")

    # Benchmart time for rapidfuzz
    fuzz_time = benchmark_rapidfuzz(x, y)
    print(f"rapidfuzz time: {fuzz_time}")
    print("Benchmark complete.")


if __name__ == "__main__":
    main()
