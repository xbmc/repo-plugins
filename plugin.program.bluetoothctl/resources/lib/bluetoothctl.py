from __future__ import annotations
from typing import Any
import subprocess
from subprocess import CompletedProcess


class Bluetoothctl:
    """Interact with the 'bluetoothctl' utility."""

    # Default arguments to pass to subprocess.run
    _run_args: dict[str, Any] = {
        'capture_output': True,
        'encoding': 'utf8',
    }

    def __init__(self, executable: str = '/usr/bin/bluetoothctl',
                 scan_timeout: int = 5) -> None:
        """
        Construct a Bluetoothctl instance.

        executable: Path to the bluetoothctl executable on the host.
        scan_timeout: Time (in seconds) to spend scanning for available
            devices.
        """
        self._executable = executable
        self.scan_timeout = scan_timeout

    @property
    def executable(self) -> str:
        """Return the path to the bluetoothctl executable"""
        return self._executable

    def scan(self) -> CompletedProcess[str]:
        """
        Scan for available devices.

        Returns: A CompletedProcess instance containing the result of the
            command.
        """
        command = [self.executable, '--timeout', str(self.scan_timeout),
                   'scan', 'on']
        return subprocess.run(command, **self._run_args)

    def get_devices(self) -> CompletedProcess[Any]:
        """
        List available devices.

        Returns: A CompletedProcess instance containing the result of the
            command.
        """
        command = [self.executable, 'devices']

        process = subprocess.run(command, **self._run_args)
        return process

    def get_paired_devices(self) -> CompletedProcess[Any]:
        """
        List paired devices

        Returns: A CompletedProcess instance containing the result of the
            command.
        """
        command = [self.executable, 'paired-devices']

        process = subprocess.run(command, **self._run_args)
        return process

    @staticmethod
    def parse_devices_list(stdout: str) -> dict[str, str]:
        """
        Identify devices from bluetoothctl `devices` or `paired-devices`
        output.

        Returns: Dict of friendly_name: device_address.
        """
        # The stdout of 'bluetoothctl devices' is in the format
        # Device <device_address> <friendly_name>
        devices = {
            item[2]: item[1] for item in
            (line.split() for line in stdout.splitlines())
        }

        return devices

    def connect(self, address: str) -> CompletedProcess[str]:
        """
        Connect to a device.

        Returns: A CompletedProcess instance containing the result of the
            command.
        """
        command = [self.executable, 'connect', address]
        return subprocess.run(command, **self._run_args)

    def disconnect(self, address: str) -> CompletedProcess[str]:
        """
        Disconnect from a device.

        Returns: A CompletedProcess instance containing the result of the
            command.
        """
        command = [self.executable, 'disconnect', address]
        return subprocess.run(command, **self._run_args)

    def pair(self, address: str) -> CompletedProcess[str]:
        """
        Pair with a device.

        This method only support non-interactive pairing.

        Returns: A CompletedProcess instance containing the result of the
            command.
        """
        command = [self.executable, 'pair', address]
        return subprocess.run(command, **self._run_args)

    def remove(self, address: str) -> CompletedProcess[str]:
        """
        Remove device (revoke pairing).

        Returns: A CompletedProcess instance containing the result of the
            command.
        """
        command = [self.executable, 'remove', address]
        return subprocess.run(command, **self._run_args)

    def trust(self, address: str) -> CompletedProcess[str]:
        """
        Trust a device.

        Returns: A CompletedProcess instance containing the result of the
            command.
        """
        command = [self.executable, 'trust', address]
        return subprocess.run(command, **self._run_args)

    def untrust(self, address: str) -> CompletedProcess[str]:
        """
        Revoke trust in a device.

        Returns: A CompletedProcess instance containing the result of the
            command.
        """
        command = [self.executable, 'untrust', address]
        return subprocess.run(command, **self._run_args)

    def info(self, address: str) -> CompletedProcess[str]:
        """
        Get device information.

        Returns: A CompletedProcess instance containing the result of the
            command.
        """
        command = [self.executable, 'info', address]
        return subprocess.run(command, **self._run_args)
