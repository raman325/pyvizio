"""Tests for pyvizio constants validation."""

from pyvizio.const import (
    APP_HOME,
    APPS,
    DEFAULT_PORTS,
    DEFAULT_TIMEOUT,
    DEVICE_CLASS_CRAVE360,
    DEVICE_CLASS_SPEAKER,
    DEVICE_CLASS_TV,
    EQUIVALENT_NAME_SPACES,
    MAX_VOLUME,
)


class TestAppsListStructure:
    def test_apps_list_not_empty(self):
        assert len(APPS) > 0

    def test_apps_have_required_keys(self):
        for app in APPS:
            assert "name" in app, f"App missing 'name': {app}"
            assert "country" in app, f"App missing 'country': {app.get('name')}"
            assert "config" in app, f"App missing 'config': {app.get('name')}"

    def test_apps_config_structure(self):
        for app in APPS:
            configs = app["config"]
            assert isinstance(configs, list), f"Config not a list for {app['name']}"
            for config in configs:
                assert "APP_ID" in config, f"Config missing APP_ID for {app['name']}"
                assert "NAME_SPACE" in config, (
                    f"Config missing NAME_SPACE for {app['name']}"
                )

    def test_apps_country_is_list(self):
        for app in APPS:
            assert isinstance(app["country"], list), (
                f"Country not list for {app['name']}"
            )


class TestDeviceClassConstants:
    def test_device_class_tv(self):
        assert DEVICE_CLASS_TV == "tv"

    def test_device_class_speaker(self):
        assert DEVICE_CLASS_SPEAKER == "speaker"

    def test_device_class_crave360(self):
        assert DEVICE_CLASS_CRAVE360 == "crave360"


class TestMaxVolume:
    def test_tv_max_volume(self):
        assert MAX_VOLUME[DEVICE_CLASS_TV] == 100

    def test_speaker_max_volume(self):
        assert MAX_VOLUME[DEVICE_CLASS_SPEAKER] == 31

    def test_crave360_max_volume(self):
        assert MAX_VOLUME[DEVICE_CLASS_CRAVE360] == 100

    def test_all_device_types_have_max_volume(self):
        for dt in (DEVICE_CLASS_TV, DEVICE_CLASS_SPEAKER, DEVICE_CLASS_CRAVE360):
            assert dt in MAX_VOLUME


class TestDefaults:
    def test_default_ports_defined(self):
        assert isinstance(DEFAULT_PORTS, list)
        assert len(DEFAULT_PORTS) > 0
        assert all(isinstance(p, int) for p in DEFAULT_PORTS)

    def test_default_timeout_positive(self):
        assert DEFAULT_TIMEOUT > 0

    def test_app_home_defined(self):
        assert APP_HOME is not None
        assert "name" in APP_HOME
        assert "config" in APP_HOME

    def test_equivalent_name_spaces(self):
        assert 2 in EQUIVALENT_NAME_SPACES
        assert 4 in EQUIVALENT_NAME_SPACES
