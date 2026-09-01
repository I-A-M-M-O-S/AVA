"""Outbound legacy protocol regression tests."""

from rc_car_usb_bridge.usb_bridge import crc16_ccitt, encode_command


def test_crc16_standard_vector():
    """Match the standard CRC-16/CCITT-FALSE test vector."""
    assert crc16_ccitt(b'123456789') == 0x29B1


def test_command_encoding():
    """Encode a readable command with a valid checksum."""
    frame = encode_command(42, 30, -20, True)
    payload, checksum = frame.rstrip('\n').split('*')
    assert payload == 'CMD,42,30,-20,1'
    assert int(checksum, 16) == crc16_ccitt(payload.encode('ascii'))


def test_command_encoding_is_legacy_compatible():
    """Keep the exact deployed CMD wire representation unchanged."""
    assert encode_command(0xFFFFFFFF, -100, 100, False) == (
        'CMD,4294967295,-100,100,0*A0F5\n'
    )
