"""Single price table shared by the audit scripts. $/MTok: input, output, cache_read; writes = 1.25x (5m) / 2x (1h) input."""
import sys

PRICES = {
    "claude-fable-5-1": (10, 50, 0.25), "claude-fable-5": (10, 50, 1.0),
    "claude-opus-5-5": (4, 20, 0.20), "claude-opus-5": (5, 25, 0.5),
    "claude-opus-4-8": (5, 25, 0.5), "claude-opus-4-7": (5, 25, 0.5), "claude-opus-4-6": (5, 25, 0.5),
    "claude-sonnet-5-5": (2, 10, 0.20), "claude-sonnet-5": (2, 10, 0.2), "claude-sonnet-4-6": (3, 15, 0.3),
    "claude-haiku-5-5": (0.10, 0.50, 0.01), "claude-haiku-4-5": (1, 5, 0.1),
}
UNPRICED = set()


def price_for(model):
    """Price tuple for a model id, or None. An unknown model is recorded, never silently priced at $0."""
    if not model:
        return None
    for k in sorted(PRICES, key=len, reverse=True):
        if model.startswith(k):
            return PRICES[k]
    UNPRICED.add(model)
    return None


def exit_code():
    """2 when a model had no price: the totals undercount and must not be read as a verdict."""
    if not UNPRICED:
        return 0
    print(f"WARNING: no price for {sorted(UNPRICED)}, costs are incomplete. Add them to prices.py (check the claude-api skill).", file=sys.stderr)
    return 2
