from typing import Any

import requests

BASE_URL = "https://api.e-stat.go.jp/rest/3.0/app/json"


class EStatAPIError(RuntimeError):
    """e-Stat APIの取得に失敗した場合の例外。"""


def _request(
    endpoint: str,
    response_key: str,
    params: dict[str, str],
    timeout: int,
) -> dict[str, Any]:
    """GET・JSON解析・e-Statステータス確認を共通化する。"""
    try:
        response = requests.get(
            f"{BASE_URL}/{endpoint}",
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise EStatAPIError("e-Stat APIへの接続に失敗しました。") from exc

    try:
        data = response.json()
    except requests.JSONDecodeError as exc:
        raise EStatAPIError("APIレスポンスをJSONとして解析できませんでした。") from exc

    result = data[response_key]["RESULT"]

    if int(result["STATUS"]) != 0:
        raise EStatAPIError(f"APIエラー: {result.get('ERROR_MSG', '詳細不明')}")

    return data


def get_meta_info(
    app_id: str,
    stats_data_id: str,
    timeout: int = 30,
) -> dict[str, Any]:
    """指定した統計表のメタ情報を取得する。"""

    params = {
        "appId": app_id,
        "statsDataId": stats_data_id,
        "lang": "J",
    }

    return _request("getMetaInfo", "GET_META_INFO", params, timeout)


def get_stats_data(
    app_id: str,
    stats_data_id: str,
    filters: dict[str, str] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """指定した条件で統計データを取得する。"""

    params = {
        "appId": app_id,
        "statsDataId": stats_data_id,
        "lang": "J",
        "metaGetFlg": "Y",
        "cntGetFlg": "N",
    }

    if filters:
        params.update(filters)

    return _request("getStatsData", "GET_STATS_DATA", params, timeout)
