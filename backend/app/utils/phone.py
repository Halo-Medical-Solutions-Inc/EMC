def normalize_phone_digits(phone: str) -> str:
    return "".join(c for c in phone if c.isdigit())


def is_practice_main_line_caller(phone: str) -> bool:
    digits = normalize_phone_digits(phone)
    return len(digits) >= 10 and digits.endswith("5594865000")
