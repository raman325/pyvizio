"""Tests for AppConfig and find_app_name."""

from pyvizio.api.apps import AppConfig, find_app_name
from pyvizio.const import APP_CAST, APP_HOME, APPS, NO_APP_RUNNING, UNKNOWN_APP


class TestAppConfig:
    def test_init_defaults(self):
        config = AppConfig()
        assert config.APP_ID is None
        assert config.NAME_SPACE is None
        assert config.MESSAGE is None

    def test_init_with_values(self):
        config = AppConfig("1", 3, "http://example.com")
        assert config.APP_ID == "1"
        assert config.NAME_SPACE == 3
        assert config.MESSAGE == "http://example.com"

    def test_equality_same_values(self):
        a = AppConfig("1", 3, None)
        b = AppConfig("1", 3, None)
        assert a == b

    def test_equality_different_values(self):
        a = AppConfig("1", 3, None)
        b = AppConfig("2", 3, None)
        assert a != b

    def test_equality_self(self):
        a = AppConfig("1", 3, None)
        assert a == a

    def test_bool_truthy(self):
        config = AppConfig("1", 3, None)
        assert bool(config) is True

    def test_bool_falsy(self):
        config = AppConfig()
        assert bool(config) is False

    def test_repr(self):
        config = AppConfig("1", 3, None)
        r = repr(config)
        assert "AppConfig" in r
        assert "APP_ID" in r

    def test_bool_partial_values_truthy(self):
        config = AppConfig(APP_ID="1")
        assert bool(config) is True


class TestFindAppName:
    def test_exact_match(self):
        apps = [
            {"name": "Netflix", "config": [{"APP_ID": "1", "NAME_SPACE": 3}]},
        ]
        config = AppConfig("1", 3, None)
        assert find_app_name(config, apps) == "Netflix"

    def test_list_config_match(self):
        apps = [
            {
                "name": "TestApp",
                "config": [
                    {"APP_ID": "10", "NAME_SPACE": 2},
                    {"APP_ID": "11", "NAME_SPACE": 3},
                ],
            },
        ]
        config = AppConfig("11", 3, None)
        assert find_app_name(config, apps) == "TestApp"

    def test_equivalent_namespace_match(self):
        """NAME_SPACE 2 and 4 are equivalent."""
        apps = [
            {"name": "TestApp", "config": [{"APP_ID": "42", "NAME_SPACE": 2}]},
        ]
        config = AppConfig("42", 4, None)
        assert find_app_name(config, apps) == "TestApp"

    def test_equivalent_namespace_reverse(self):
        """NAME_SPACE 4 in list, 2 in config."""
        apps = [
            {"name": "TestApp", "config": [{"APP_ID": "42", "NAME_SPACE": 4}]},
        ]
        config = AppConfig("42", 2, None)
        assert find_app_name(config, apps) == "TestApp"

    def test_unknown_app(self):
        apps = [
            {"name": "Netflix", "config": [{"APP_ID": "1", "NAME_SPACE": 3}]},
        ]
        config = AppConfig("999", 99, None)
        assert find_app_name(config, apps) == UNKNOWN_APP

    def test_no_app_running_none(self):
        assert find_app_name(None, APPS) == NO_APP_RUNNING

    def test_no_app_running_empty_config(self):
        assert find_app_name(AppConfig(), APPS) == NO_APP_RUNNING

    def test_namespace_zero_returns_cast(self):
        config = AppConfig("anything", 0, None)
        assert find_app_name(config, []) == APP_CAST

    def test_app_home_match(self):
        config = AppConfig("1", 4, "http://127.0.0.1:12345/scfs/sctv/main.html")
        assert find_app_name(config, [APP_HOME]) == "SmartCast Home"

    def test_dict_config_match(self):
        """Test with dict config instead of list config."""
        apps = [
            {"name": "DictApp", "config": {"APP_ID": "5", "NAME_SPACE": 2}},
        ]
        config = AppConfig("5", 2, None)
        assert find_app_name(config, apps) == "DictApp"
