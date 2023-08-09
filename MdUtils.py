def value_to_bool(value):
    return value.lower() == 'true' if isinstance(value, str) else bool(value)

VIVID_COLOR_LIST =  [
    "#0000FF",  # Blue
    "#FF0000",  # Red
    "#008000",  # Green
    "#800080",  # Purple
    "#FFA500",  # Orange
    "#00FFFF",  # Cyan
    "#FF00FF",  # Magenta
    "#FFFF00",  # Yellow
    "#008080",  # Teal
    "#FF1493",  # Pink
    "#00FF00",  # Lime
    "#4B0082",  # Indigo
    "#800000",  # Maroon
    "#808000",  # Olive
    "#000080",  # Navy
    "#FF6F61",  # Coral
    "#40E0D0",  # Turquoise
    "#E6E6FA",  # Lavender
    "#FFD700",  # Gold
    "#6A5ACD"   # Slate
]
PASTEL_COLOR_LIST = [
    "#AEC6CF",  # Pastel Blue
    "#F49AC2",  # Pastel Pink
    "#B0E57C",  # Pastel Green
    "#B39EB5",  # Pastel Purple
    "#F9CB9C",  # Pastel Orange
    "#F8ED8E",  # Pastel Yellow
    "#DCD0FF",  # Pastel Lavender
    "#AAF0D1",  # Pastel Mint
    "#FFD1A3",  # Pastel Peach
    "#AEEEEE",  # Pastel Aqua
    "#E8A3E5",  # Pastel Lilac
    "#FFB5B5",  # Pastel Coral
    "#94E8B4",  # Pastel Teal
    "#FF9E9E",  # Pastel Salmon
    "#87CEEB",  # Pastel Sky Blue
    "#FFC7E5",  # Pastel Rose
    "#FDFD96",  # Pastel Lemon
    "#C5A3FF",  # Pastel Periwinkle
    "#AFEEEE",  # Pastel Turquoise
    "#FFD8B1"   # Pastel Apricot
]