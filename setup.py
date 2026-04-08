"""Development setup for dorker."""

from setuptools import setup, find_packages

setup(
    name="dorker",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "dorker=dorker.cli:main",
        ],
    },
)
