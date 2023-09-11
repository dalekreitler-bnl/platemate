import numpy as np


def generate_uppercase_alphabets(n: int) -> list:
    if n < 1:
        raise ValueError("The number must be a positive integer.")

    alphabets = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def get_letter(num):
        result = []
        while num > 0:
            num, remainder = divmod(num - 1, 26)
            result.append(alphabets[remainder])
        return "".join(reversed(result))

    return [get_letter(i) for i in range(1, n + 1)]


def generate_array(start, stop, step, replicates):
    # Generate an array from start to stop with the given step
    arr = np.arange(start, stop + step, step)

    # Repeat each number in the array by the specified replicates
    repeated_arr = np.repeat(arr, replicates)

    return np.ndarray.tolist(repeated_arr)
