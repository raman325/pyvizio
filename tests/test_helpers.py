"""Tests for pyvizio.helpers module."""

import asyncio

from pyvizio.helpers import async_to_sync, dict_get_case_insensitive, get_value_from_path


class TestDictGetCaseInsensitive:
    def test_exact_match(self):
        assert dict_get_case_insensitive({"key": "value"}, "key") == "value"

    def test_mixed_case_key(self):
        assert dict_get_case_insensitive({"Key": "value"}, "key") == "value"

    def test_mixed_case_lookup(self):
        assert dict_get_case_insensitive({"key": "value"}, "KEY") == "value"

    def test_missing_key_returns_none(self):
        assert dict_get_case_insensitive({"key": "value"}, "other") is None

    def test_missing_key_returns_default(self):
        assert dict_get_case_insensitive({"key": "value"}, "other", "default") == "default"

    def test_default_none_explicit(self):
        assert dict_get_case_insensitive({"a": 1}, "b", None) is None

    def test_numeric_value(self):
        assert dict_get_case_insensitive({"COUNT": 42}, "count") == 42

    def test_nested_dict_value(self):
        inner = {"nested": True}
        assert dict_get_case_insensitive({"DATA": inner}, "data") == inner


class TestGetValueFromPath:
    def test_single_level_path(self):
        data = {"model_name": "V505-G9"}
        paths = [["model_name"]]
        assert get_value_from_path(data, paths) == "V505-G9"

    def test_single_level_case_insensitive(self):
        data = {"MODEL_NAME": "V505-G9"}
        paths = [["model_name"]]
        assert get_value_from_path(data, paths) == "V505-G9"

    def test_missing_path_returns_none(self):
        data = {"other": "value"}
        paths = [["model_name"]]
        assert get_value_from_path(data, paths) is None

    def test_multiple_paths_first_match(self):
        data = {"model_name": "V505-G9"}
        paths = [["model_name"], ["system_info", "model_name"]]
        assert get_value_from_path(data, paths) == "V505-G9"

    def test_empty_data(self):
        assert get_value_from_path({}, [["key"]]) is None

    def test_empty_paths(self):
        assert get_value_from_path({"key": "val"}, []) is None


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
