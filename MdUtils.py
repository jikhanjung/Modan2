def value_to_bool(value):
    return value.lower() == 'true' if isinstance(value, str) else bool(value)
