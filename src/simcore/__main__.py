"""Runs when you type `python3 -m simcore`: prints the environment versions."""

from simcore import environment_info

for name, version in environment_info().items():
    print(f"{name:13s} {version}")
