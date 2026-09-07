"""e-Statレスポンスの形式を扱う共通処理。"""

from typing import Any


def ensure_list(value: Any) -> list[Any]:
    """値を必ずリストとして返す。"""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]
