from typing import Any

import requests


BASE_URL = "https://api.e-stat.go.jp/rest/3.0/app/json"


class EStatAPIError(RuntimeError):
    """e-Stat APIの取得に失敗した場合の例外。"""


def get_meta_info(
    app_id: str,
    stats_data_id: str,
    timeout: int = 30,
) -> dict[str, Any]:
    """指定した統計表のメタ情報を取得する。"""

    url = f"{BASE_URL}/getMetaInfo"

    params = {
        "appId": app_id,
        "statsDataId": stats_data_id,
        "lang": "J",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise EStatAPIError(
            "e-Stat APIへの接続に失敗しました。"
        ) from exc

    try:
        data = response.json()
    except requests.JSONDecodeError as exc:
        raise EStatAPIError(
            "APIレスポンスをJSONとして解析できませんでした。"
        ) from exc

    result = data["GET_META_INFO"]["RESULT"]

    if int(result["STATUS"]) != 0:
        raise EStatAPIError(
            f'APIエラー: {result.get("ERROR_MSG", "詳細不明")}'
        )

    return data