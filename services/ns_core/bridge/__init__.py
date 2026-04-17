"""NS∞ bridge normalization — every upstream response wrapped in ReturnBlock.v2."""
from .normalize import wrap_response, normalize_bridge_response

__all__ = ["wrap_response", "normalize_bridge_response"]
