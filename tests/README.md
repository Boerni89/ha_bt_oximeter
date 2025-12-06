# Bluetooth Oximeter Tests

This directory contains the test suite for the bt_oximeter custom component, following the style and best practices from the [ics_calendar](https://github.com/franc6/ics_calendar) project.

## Test Organization

Tests are organized using class-based structure for better organization and readability:

```python
class TestBTOximeterConfigFlow:
    """Test BTOximeterConfigFlow class."""

    @pytest.mark.asyncio
    async def test_bluetooth_discovery(self, hass, jks50f_service_info):
        """Test discovery via bluetooth."""
        # Arrange
        # Act
        result = await hass.config_entries.flow.async_init(...)
        # Assert
        pytest.helpers.assert_flow_form_shown(result, "bluetooth_confirm")
```

## Custom pytest Helpers

The test suite uses custom pytest helpers for cleaner assertions:

- `pytest.helpers.assert_config_entry_created(result, "OXIMETER")` - Assert config entry was created
- `pytest.helpers.assert_flow_form_shown(result, "bluetooth_confirm")` - Assert flow shows form
- `pytest.helpers.assert_flow_aborted(result, "not_supported")` - Assert flow was aborted

These helpers are defined in `conftest.py` using `@pytest.helpers.register`.

## Setup

Install development dependencies:

```bash
pip install -r requirements_dev.txt
```

## Running Tests

### All tests
```bash
cd /workspaces/core/config/custom_components/bt_oximeter
pytest tests/ -v
```

### Using the test script (recommended)
```bash
chmod +x test.sh
./test.sh
```

Or test specific file:
```bash
./test.sh tests/test_config_flow.py
```

### With coverage
```bash
pytest tests/ --cov=custom_components.bt_oximeter --cov-report=html --cov-report=term-missing
```

Coverage report will be in `htmlcov/index.html`.

### Specific test
```bash
pytest tests/test_config_flow.py::TestBTOximeterConfigFlow::test_bluetooth_discovery -v
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                        # Fixtures and pytest helpers
├── pytest.ini                         # Pytest configuration
├── README.md                          # This file
├── test_config_flow.py               # Config flow tests (class-based)
├── test_sensor.py                    # Sensor platform tests (class-based)
└── test_binary_sensor.py             # Binary sensor platform tests (class-based)
```

## Available Fixtures

Defined in `conftest.py`:

- **`hass`** - Home Assistant instance (from pytest-homeassistant-custom-component)
- **`mock_bleak_client`** - Mocked BleakClient for Bluetooth communication
- **`jks50f_service_info`** - BluetoothServiceInfoBleak for JKS50F device
- **`unsupported_service_info`** - BluetoothServiceInfoBleak for unsupported device

## Test Patterns

### Arrange-Act-Assert Pattern

Tests follow the AAA pattern with clear comments:

```python
@pytest.mark.asyncio
async def test_example(self, hass, jks50f_service_info):
    """Test description."""
    # Arrange
    setup_data = {...}

    # Act
    result = await perform_action()

    # Assert
    pytest.helpers.assert_config_entry_created(result, "OXIMETER")
```

### Class Organization

Each test module uses a test class:

- `TestBTOximeterConfigFlow` - Config flow tests
- `TestBTOximeterSensor` - Sensor platform tests
- `TestBTOximeterBinarySensor` - Binary sensor platform tests

## Style Guidelines

Following ics_calendar project conventions:

1. **Class-based organization** - All tests in classes
2. **Custom pytest helpers** - Reusable assertions via `@pytest.helpers.register`
3. **Arrange-Act-Assert** - Clear test structure with comments
4. **Async tests** - Marked with `@pytest.mark.asyncio`
5. **Descriptive docstrings** - Every test has a clear description
6. **Type hints** - Parameters include type annotations

## Coverage Goals

- Overall: >70%
- Config flow: >80%
- Core modules (coordinator, device): >60%

Current coverage can be viewed by running tests with coverage and opening `htmlcov/index.html`.

## Dependencies

- `pytest>=7.4.0` - Test framework
- `pytest-homeassistant-custom-component>=0.13.0` - HA test helpers
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-helpers-namespace>=2021.12.29` - Custom test helpers
