# --- Null Object Definition (No change needed here) ---

class NullMapping:
    """
    A Null Object representing an empty, immutable mapping.
    Provides the necessary interface for the process_style function
    (items, update, __contains__, __getitem__, get, __len__).
    """
    _instance = None

    # Optional: Singleton pattern
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NullMapping, cls).__new__(cls)
        return cls._instance

    # Method potentially used by dict()
    def items(self):
        return iter([])

    # Method needed for 'key in mapping' check
    def __contains__(self, key):
        return False

    # Method needed for mapping[key] access (raises error like a dict)
    def __getitem__(self, key):
        raise KeyError(key)

NULL_MAPPING = NullMapping()

# --- Original Data Structures ---
STYLE = {"L1 question": "question"}
EXTENDER = {"L2 answer": "answer"}

def process_style(length: int, style: str, mapping=NULL_MAPPING):
    """
    Combines conditional mapping extension and style normalization,
    using the Null Object pattern for the default mapping.

    Prioritizes exact match in the effective mapping before falling back
    to substring checks.

    Args:
        length: An integer influencing mapping usage. If > 100, EXTENDER is added.
        style: The input style string to normalize.
        mapping: An optional dictionary-like mapping. Defaults to NULL_MAPPING.

    Returns:
        The normalized style string.
    """
    effective_mapping = mapping
    if length > 100:
        if mapping is NULL_MAPPING:
            combined_mapping = {}
        else:
            combined_mapping = dict(mapping)

        # Now update the combined_mapping (which is guaranteed to be a dict)
        combined_mapping.update(EXTENDER)
        effective_mapping = combined_mapping

    if style in effective_mapping:
         return effective_mapping[style]
    else:
        if "question" in style:
            return "question"
        elif "answer" in style:
            return "answer"
        else:
            return style

# --- Example Usage (Should now work) ---

print("--- Using Default (Null) Mapping ---")
print(f"Input: Style='L1 question', Length=50  | Output: {process_style(50, 'L1 question')}")
# This call previously caused the error:
print(f"Input: Style='L2 answer', Length=150    | Output: {process_style(150, 'L2 answer')}")
print(f"Input: Style='other style', Length=150 | Output: {process_style(150, 'other style')}")
print(f"Input: Style='some question', Length=50| Output: {process_style(50, 'some question')}")

print("\n--- Providing STYLE Mapping ---")
print(f"Input: Style='L1 question', Length=50  | Output: {process_style(50, 'L1 question', STYLE)}")
print(f"Input: Style='L1 question', Length=150 | Output: {process_style(150, 'L1 question', STYLE)}")
print(f"Input: Style='L2 answer', Length=50    | Output: {process_style(50, 'L3 answer', STYLE)}")
print(f"Input: Style='L2 answer', Length=150   | Output: {process_style(150, 'L3 answer', STYLE)}")
print(f"Input: Style='another style', Length=150| Output: {process_style(150, 'another style', STYLE)}")