def normalize_rimworld_version(raw: str) -> float:
    result = raw.lower()
    result = result.replace("v", "")
    digits, *_ = result.split(" ", 1)
    digits = result.split(".")
    digits = [int(item) for item in digits[:2]]
    digits = (digits + [0, 0])[:2]
    major, minor = digits
    return float(f"{major}.{minor}")
