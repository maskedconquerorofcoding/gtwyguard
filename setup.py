from setuptools import setup, find_packages

setup(
    name="gtwyguard",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "watchdog>=3.0.0",
        "rich>=12.0.0"
    ],
    entry_points={
        "console_scripts": [
            "gtwyguard=gtwyguard.cli:main"
        ]
    }
)
