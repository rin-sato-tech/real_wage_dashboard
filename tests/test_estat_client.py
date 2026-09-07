from unittest.mock import Mock

import pytest
import requests

from real_wage_dashboard.estat_client import (
    BASE_URL,
    EStatAPIError,
    get_meta_info,
    get_stats_data,
)


@pytest.fixture(
    params=[
        (get_meta_info, "getMetaInfo", "GET_META_INFO"),
        (get_stats_data, "getStatsData", "GET_STATS_DATA"),
    ]
)
def endpoint(request):
    return request.param


def test_requests_preserve_endpoint_params_timeout_and_response(monkeypatch, endpoint):
    call, name, key = endpoint
    payload = {key: {"RESULT": {"STATUS": "0"}, "data": [1, 2]}}
    response = Mock()
    response.json.return_value = payload
    get = Mock(return_value=response)
    monkeypatch.setattr(requests, "get", get)

    kwargs = {"app_id": "test-app", "stats_data_id": "test-table", "timeout": 7}
    params = {"appId": "test-app", "statsDataId": "test-table", "lang": "J"}
    if call is get_stats_data:
        # Existing filters can override the default request flags.
        kwargs["filters"] = {"cdCat01": "0163", "metaGetFlg": "N"}
        params.update({"metaGetFlg": "N", "cntGetFlg": "N", "cdCat01": "0163"})

    assert call(**kwargs) is payload
    get.assert_called_once_with(f"{BASE_URL}/{name}", params=params, timeout=7)
    response.raise_for_status.assert_called_once_with()


@pytest.mark.parametrize(
    "failure", ["connection", "http", "json", "api", "api_without_message"]
)
def test_requests_preserve_error_messages_and_causes(monkeypatch, endpoint, failure):
    call, _, key = endpoint
    response = Mock()
    get = Mock(return_value=response)
    monkeypatch.setattr(requests, "get", get)
    cause = None

    if failure == "connection":
        cause = requests.Timeout("timed out")
        get.side_effect = cause
        message = "e-Stat APIへの接続に失敗しました。"
    elif failure == "http":
        cause = requests.HTTPError("server error")
        response.raise_for_status.side_effect = cause
        message = "e-Stat APIへの接続に失敗しました。"
    elif failure == "json":
        cause = requests.JSONDecodeError("invalid", "?", 0)
        response.json.side_effect = cause
        message = "APIレスポンスをJSONとして解析できませんでした。"
    else:
        result = {"STATUS": 100}
        if failure == "api":
            result["ERROR_MSG"] = "対象なし"
        response.json.return_value = {key: {"RESULT": result}}
        message = "APIエラー: " + result.get("ERROR_MSG", "詳細不明")

    with pytest.raises(EStatAPIError) as error:
        call("test-app", "test-table")
    assert str(error.value) == message
    assert error.value.__cause__ is cause
