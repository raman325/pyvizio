"""Tests for pyvizio.helpers module."""

import pytest

from pyvizio.helpers import (
    async_to_sync,
    dict_get_case_insensitive,
    get_value_from_path,
)


class TestDictGetCaseInsensitive:
    @pytest.mark.parametrize(
        "data,key,expected",
        [
            ({"key": "value"}, "key", "value"),
            ({"Key": "value"}, "key", "value"),
            ({"key": "value"}, "KEY", "value"),
            ({"COUNT": 42}, "count", 42),
            ({"DATA": {"nested": True}}, "data", {"nested": True}),
        ],
    )
    def test_found(self, data, key, expected):
        assert dict_get_case_insensitive(data, key) == expected

    @pytest.mark.parametrize("default", [None, "fallback"])
    def test_missing_key_returns_default(self, default):
        assert (
            dict_get_case_insensitive({"key": "value"}, "other", default) is default
            or dict_get_case_insensitive({"key": "value"}, "other", default) == default
        )


class TestGetValueFromPath:
    def test_single_level_path(self):
        assert (
            get_value_from_path({"model_name": "V505-G9"}, [["model_name"]])
            == "V505-G9"
        )

    def test_single_level_case_insensitive(self):
        assert (
            get_value_from_path({"MODEL_NAME": "V505-G9"}, [["model_name"]])
            == "V505-G9"
        )

    def test_missing_path_returns_none(self):
        assert get_value_from_path({"other": "value"}, [["model_name"]]) is None

    def test_multiple_paths_first_match(self):
        data = {"model_name": "V505-G9"}
        paths = [["model_name"], ["model"]]
        assert get_value_from_path(data, paths) == "V505-G9"

    def test_multiple_paths_fallback(self):
        """Second path matches when first doesn't."""
        data = {"model": "V505-G9"}
        paths = [["model_name"], ["model"]]
        assert get_value_from_path(data, paths) == "V505-G9"

    @pytest.mark.parametrize(
        "data,paths",
        [
            ({}, [["key"]]),
            ({"key": "val"}, []),
        ],
    )
    def test_returns_none(self, data, paths):
        assert get_value_from_path(data, paths) is None


class TestAsyncToSync:
    def test_converts_async_to_sync(self):
        async def async_add(a, b):
            return a + b

        sync_add = async_to_sync(async_add)
        assert sync_add(2, 3) == 5

    def test_preserves_function_name(self):
        async def my_func():
            pass

        wrapped = async_to_sync(my_func)
        assert wrapped.__name__ == "my_func"

    def test_handles_none_return(self):
        async def returns_none():
            return None

        sync_func = async_to_sync(returns_none)
        assert sync_func() is None
