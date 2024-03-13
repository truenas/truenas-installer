import io
from unittest.mock import Mock, patch

import pytest

from truenas_installer.serial import serial_sql


@pytest.mark.asyncio
async def test__serial_sql():
    async def run(args, **kwargs):
        return Mock(stdout={
            "dmesg": "[    0.613041] 00:07: ttyS0 at I/O 0x3f8 (irq = 4, base_baud = 115200) is a 16550",
            "setserial -G /dev/ttyS0": "/dev/ttyS0 uart 16550A port 0x03f8 irq 4 baud_base 115200 spd_normal skip_test",
        }[" ".join(args)])

    with patch("truenas_installer.serial.open", lambda path: io.StringIO("console=ttyS")):
        with patch("truenas_installer.serial.run", run):
            assert await serial_sql() == ("update system_advanced set adv_serialconsole = 1;"
                                          "update system_advanced set adv_serialport = 'ttyS0';"
                                          "update system_advanced set adv_serialspeed = 115200;")
