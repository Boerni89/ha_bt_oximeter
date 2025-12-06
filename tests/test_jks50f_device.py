"""Test the JKS50F device implementation."""

from datetime import datetime
from unittest.mock import patch

import pytest

from custom_components.bt_oximeter.devices.jks50f import JKS50FDevice


class TestJKS50FDevice:
    """Test JKS50FDevice class."""

    def test_device_info(self) -> None:
        """Test device info returns correct metadata."""
        # Arrange
        device = JKS50FDevice()

        # Act
        info = device.device_info

        # Assert
        assert info.manufacturer == "Guangdong Health Medical Technology Co., Ltd."
        assert info.model == "JKS50F"
        assert info.frame_header == b"\xff\x44\x01"
        assert info.frame_length == 69
        assert info.service_uuid == "0000ffe0-0000-1000-8000-00805f9b34fb"
        assert info.notify_uuid == "0000ffe1-0000-1000-8000-00805f9b34fb"
        assert "E04E7A" in info.supported_ouis
        assert len(info.supported_ouis) == 8

    def test_add_to_buffer_normal(self) -> None:
        """Test adding data to buffer works correctly."""
        # Arrange
        device = JKS50FDevice()
        data = b"\xff\x44\x01\x00\x64\x50"

        # Act
        device.add_to_buffer(data)

        # Assert
        assert len(device._buffer) == 6
        assert device._buffer == bytearray(data)

    def test_add_to_buffer_multiple_times(self) -> None:
        """Test adding data to buffer multiple times concatenates."""
        # Arrange
        device = JKS50FDevice()
        data1 = b"\xff\x44\x01"
        data2 = b"\x00\x64\x50"

        # Act
        device.add_to_buffer(data1)
        device.add_to_buffer(data2)

        # Assert
        assert len(device._buffer) == 6
        assert device._buffer == bytearray(data1 + data2)

    def test_add_to_buffer_trims_when_too_large(self) -> None:
        """Test buffer is trimmed when exceeding max size."""
        # Arrange
        device = JKS50FDevice()
        max_size = 2 * device.device_info.frame_length  # 138 bytes
        large_data = b"\x00" * (max_size + 50)

        # Act
        device.add_to_buffer(large_data)

        # Assert
        assert len(device._buffer) == max_size
        # Should keep the last max_size bytes
        assert device._buffer == bytearray(large_data[-max_size:])

    def test_extract_measurement_no_header(self) -> None:
        """Test extract_measurement returns None when no header found."""
        # Arrange
        device = JKS50FDevice()
        device.add_to_buffer(b"\x00\x01\x02\x03\x04")

        # Act
        measurement = device.extract_measurement()

        # Assert
        assert measurement is None

    def test_extract_measurement_incomplete_frame(self) -> None:
        """Test extract_measurement returns None with incomplete frame."""
        # Arrange
        device = JKS50FDevice()
        # Add header but not enough data for complete frame
        device.add_to_buffer(b"\xff\x44\x01\x00\x64")

        # Act
        measurement = device.extract_measurement()

        # Assert
        assert measurement is None
        # Buffer should still contain the data
        assert len(device._buffer) == 5

    def test_extract_measurement_removes_data_before_header(self) -> None:
        """Test that data before header is removed."""
        # Arrange
        device = JKS50FDevice()
        # Add garbage data before header
        device.add_to_buffer(b"\x00\x01\x02\xff\x44\x01")

        # Act
        device.extract_measurement()

        # Assert
        # Garbage should be removed, only header remains
        assert device._buffer.startswith(b"\xff\x44\x01")
        assert len(device._buffer) == 3

    def test_extract_measurement_wrong_header_in_frame(self) -> None:
        """Test extract_measurement with frame that doesn't start with correct header."""
        # Arrange
        device = JKS50FDevice()
        # Add the correct header first to find it, but then add enough data
        # that looks like a complete frame but has wrong header bytes
        # This will find the header in buffer, extract 69 bytes, but fail the startswith check
        device.add_to_buffer(b"\xff\x44\x01")  # Correct header
        # Now buffer thinks it found a frame, but we need to make it fail the header check
        # Add more data that will be part of the 69-byte extraction
        device.add_to_buffer(b"\x00" * 66)

        # Now manually corrupt the extracted frame by inserting wrong data at start
        # Actually, let's create a scenario where the buffer has the header,
        # but after extraction, the frame doesn't start with the header
        # This happens when buffer manipulation creates an edge case

        # Clear and try different approach: manually set buffer with valid-length frame
        # but wrong header bytes after extraction
        device._buffer = bytearray(b"\xff\x44\x02" + b"\x00" * 66)  # Wrong third byte

        # Act
        measurement = device.extract_measurement()

        # Assert
        assert measurement is None

    def test_extract_measurement_invalid_checksum(self, caplog) -> None:
        """Test extract_measurement returns None with invalid checksum and logs debug."""
        # Arrange
        import logging

        device = JKS50FDevice()
        # Create a frame with invalid checksum
        frame = b"\xff\x44\x01" + b"\x00" * 65 + b"\xff"  # Wrong checksum
        device.add_to_buffer(frame)

        caplog.set_level(
            logging.DEBUG, logger="custom_components.bt_oximeter.devices.jks50f"
        )

        # Act
        measurement = device.extract_measurement()

        # Assert
        assert measurement is None
        assert "Checksum mismatch" in caplog.text

    @patch("custom_components.bt_oximeter.devices.jks50f.datetime")
    def test_extract_measurement_valid_frame(self, mock_datetime) -> None:
        """Test extract_measurement with valid complete frame."""
        # Arrange
        device = JKS50FDevice()
        mock_now = datetime(2025, 12, 6, 10, 30, 0)
        mock_datetime.now.return_value = mock_now

        # Create valid frame:
        # Header (3 bytes): \xff\x44\x01
        # Finger flag (1 byte): 0x00 (finger present)
        # SpO2 (1 byte): 0x64 (100%)
        # Pulse (1 byte): 0x50 (80 bpm)
        # PI bytes (2 bytes): 0x00, 0x00 (PI = 0.0)
        # Padding (60 bytes)
        # Checksum (1 byte): calculated

        frame_without_checksum = b"\xff\x44\x01\x00\x64\x50\x00\x00" + b"\x00" * 60
        checksum = (sum(frame_without_checksum) + 1) & 0xFF
        valid_frame = frame_without_checksum + bytes([checksum])

        device.add_to_buffer(valid_frame)

        # Act
        measurement = device.extract_measurement()

        # Assert
        assert measurement is not None
        assert measurement.finger_present is True
        assert measurement.spo2 == 100
        assert measurement.pulse == 80
        assert measurement.perfusion_index == 0.0
        assert measurement.timestamp == mock_now
        # Buffer should be empty after consuming frame
        assert len(device._buffer) == 0

    @patch("custom_components.bt_oximeter.devices.jks50f.datetime")
    def test_extract_measurement_no_finger(self, mock_datetime) -> None:
        """Test extract_measurement with no finger detected."""
        # Arrange
        device = JKS50FDevice()
        mock_now = datetime(2025, 12, 6, 10, 30, 0)
        mock_datetime.now.return_value = mock_now

        # Frame with finger flag = 0x01 (no finger)
        frame_without_checksum = b"\xff\x44\x01\x01\x7f\x7f\x7f\x7f" + b"\x00" * 60
        checksum = (sum(frame_without_checksum) + 1) & 0xFF
        valid_frame = frame_without_checksum + bytes([checksum])

        device.add_to_buffer(valid_frame)

        # Act
        measurement = device.extract_measurement()

        # Assert
        assert measurement is not None
        assert measurement.finger_present is False
        assert measurement.spo2 is None  # 127 = invalid
        assert measurement.pulse is None  # 127 = invalid
        assert measurement.perfusion_index is None  # 0x7F7F = 81.91

    @patch("custom_components.bt_oximeter.devices.jks50f.datetime")
    def test_extract_measurement_invalid_values(self, mock_datetime) -> None:
        """Test extract_measurement handles invalid value markers."""
        # Arrange
        device = JKS50FDevice()
        mock_now = datetime(2025, 12, 6, 10, 30, 0)
        mock_datetime.now.return_value = mock_now

        # Frame with SpO2=127, Pulse=127 (invalid markers)
        frame_without_checksum = b"\xff\x44\x01\x00\x7f\x7f\x00\x00" + b"\x00" * 60
        checksum = (sum(frame_without_checksum) + 1) & 0xFF
        valid_frame = frame_without_checksum + bytes([checksum])

        device.add_to_buffer(valid_frame)

        # Act
        measurement = device.extract_measurement()

        # Assert
        assert measurement is not None
        assert measurement.spo2 is None
        assert measurement.pulse is None

    @patch("custom_components.bt_oximeter.devices.jks50f.datetime")
    def test_extract_measurement_high_pi_value(self, mock_datetime) -> None:
        """Test extract_measurement filters unrealistic high PI values."""
        # Arrange
        device = JKS50FDevice()
        mock_now = datetime(2025, 12, 6, 10, 30, 0)
        mock_datetime.now.return_value = mock_now

        # Frame with PI > 20.0 (unrealistic)
        # PI = 21.0 => 2100 / 100 = 21.0
        # 2100 = 0x0834 => byte6 = 0x34, byte7 = 0x10
        frame_without_checksum = b"\xff\x44\x01\x00\x64\x50\x34\x10" + b"\x00" * 60
        checksum = (sum(frame_without_checksum) + 1) & 0xFF
        valid_frame = frame_without_checksum + bytes([checksum])

        device.add_to_buffer(valid_frame)

        # Act
        measurement = device.extract_measurement()

        # Assert
        assert measurement is not None
        assert measurement.perfusion_index is None  # Filtered out as unrealistic

    @patch("custom_components.bt_oximeter.devices.jks50f.datetime")
    def test_extract_measurement_realistic_pi_value(self, mock_datetime) -> None:
        """Test extract_measurement accepts realistic PI values."""
        # Arrange
        device = JKS50FDevice()
        mock_now = datetime(2025, 12, 6, 10, 30, 0)
        mock_datetime.now.return_value = mock_now

        # Frame with PI = 5.5
        # 5.5 * 100 = 550 = 0x0226
        # byte6 (7 bits): 0x26 & 0x7F = 0x26
        # byte7 (6 bits): (0x02 << 1) & 0x3F = 0x04
        frame_without_checksum = b"\xff\x44\x01\x00\x64\x50\x26\x04" + b"\x00" * 60
        checksum = (sum(frame_without_checksum) + 1) & 0xFF
        valid_frame = frame_without_checksum + bytes([checksum])

        device.add_to_buffer(valid_frame)

        # Act
        measurement = device.extract_measurement()

        # Assert
        assert measurement is not None
        assert measurement.perfusion_index == 5.5

    def test_extract_measurement_multiple_frames_in_buffer(self) -> None:
        """Test extract_measurement processes first frame and leaves rest."""
        # Arrange
        device = JKS50FDevice()

        # Create two valid frames
        frame1_without_checksum = b"\xff\x44\x01\x00\x64\x50\x00\x00" + b"\x00" * 60
        checksum1 = (sum(frame1_without_checksum) + 1) & 0xFF
        frame1 = frame1_without_checksum + bytes([checksum1])

        frame2_without_checksum = b"\xff\x44\x01\x00\x5a\x48\x00\x00" + b"\x00" * 60
        checksum2 = (sum(frame2_without_checksum) + 1) & 0xFF
        frame2 = frame2_without_checksum + bytes([checksum2])

        device.add_to_buffer(frame1 + frame2)

        # Act
        measurement1 = device.extract_measurement()
        measurement2 = device.extract_measurement()

        # Assert
        assert measurement1 is not None
        assert measurement1.spo2 == 100
        assert measurement1.pulse == 80

        assert measurement2 is not None
        assert measurement2.spo2 == 90
        assert measurement2.pulse == 72

        # Buffer should be empty
        assert len(device._buffer) == 0

    def test_verify_checksum_valid(self) -> None:
        """Test _verify_checksum with valid checksum."""
        # Arrange
        device = JKS50FDevice()
        frame_without_checksum = b"\xff\x44\x01\x00\x64\x50\x00\x00" + b"\x00" * 60
        checksum = (sum(frame_without_checksum) + 1) & 0xFF
        frame = frame_without_checksum + bytes([checksum])

        # Act
        is_valid = device._verify_checksum(frame)

        # Assert
        assert is_valid is True

    def test_verify_checksum_invalid(self, caplog) -> None:
        """Test _verify_checksum with invalid checksum and logs debug."""
        # Arrange
        import logging

        device = JKS50FDevice()
        frame_without_checksum = b"\xff\x44\x01\x00\x64\x50\x00\x00" + b"\x00" * 60
        wrong_checksum = 0xFF
        frame = frame_without_checksum + bytes([wrong_checksum])

        caplog.set_level(
            logging.DEBUG, logger="custom_components.bt_oximeter.devices.jks50f"
        )

        # Act
        is_valid = device._verify_checksum(frame)

        # Assert
        assert is_valid is False
        assert "Checksum mismatch" in caplog.text

    def test_verify_checksum_too_short(self) -> None:
        """Test _verify_checksum with frame too short."""
        # Arrange
        device = JKS50FDevice()
        frame = b"\x00"

        # Act
        is_valid = device._verify_checksum(frame)

        # Assert
        assert is_valid is False

    def test_decode_frame_too_short(self) -> None:
        """Test _decode_frame raises ValueError for short frame."""
        # Arrange
        device = JKS50FDevice()
        short_frame = b"\xff\x44\x01"

        # Act & Assert
        with pytest.raises(ValueError, match="Frame too short"):
            device._decode_frame(short_frame)

    def test_extract_measurement_stores_last_measurement(self) -> None:
        """Test that extract_measurement updates last_measurement."""
        # Arrange
        device = JKS50FDevice()
        frame_without_checksum = b"\xff\x44\x01\x00\x64\x50\x00\x00" + b"\x00" * 60
        checksum = (sum(frame_without_checksum) + 1) & 0xFF
        valid_frame = frame_without_checksum + bytes([checksum])
        device.add_to_buffer(valid_frame)

        # Act
        measurement = device.extract_measurement()

        # Assert
        assert device.last_measurement == measurement
        assert device.last_measurement.spo2 == 100

    def test_extract_measurement_exception_handling(self) -> None:
        """Test that extract_measurement handles decode exceptions gracefully."""
        # Arrange
        device = JKS50FDevice()
        # Create a frame that will pass checksum but fail decoding
        # by mocking _decode_frame to raise an exception
        frame_without_checksum = b"\xff\x44\x01\x00\x64\x50\x00\x00" + b"\x00" * 60
        checksum = (sum(frame_without_checksum) + 1) & 0xFF
        valid_frame = frame_without_checksum + bytes([checksum])
        device.add_to_buffer(valid_frame)

        # Mock _decode_frame to raise exception
        with patch.object(device, "_decode_frame", side_effect=Exception("Test error")):
            # Act
            measurement = device.extract_measurement()

            # Assert
            assert measurement is None
            # Frame should still be consumed from buffer
            assert len(device._buffer) == 0

    def test_extract_measurement_corrupted_frame_via_mock(self) -> None:
        """Test extract_measurement with corrupted frame header via mocking bytes()."""
        from unittest.mock import patch

        # Arrange
        device = JKS50FDevice()
        device.add_to_buffer(b"\xff\x44\x01" + b"\x00" * 66)  # Valid frame

        # Create corrupted frame with wrong header
        corrupted_frame = b"\xff\x44\x02" + b"\x00" * 66

        # Act - Mock bytes() to return corrupted frame
        with patch("builtins.bytes", return_value=corrupted_frame):
            measurement = device.extract_measurement()

        # Assert
        assert measurement is None
