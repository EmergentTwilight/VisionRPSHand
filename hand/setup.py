#!/usr/bin/env python
"""
Setup script for STServo Python package
"""

from setuptools import setup, find_packages
import os

# Read README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="stservo",
    version="1.0.0",
    author="iltlo",
    author_email="iltlo@connect.hku.hk",
    description="Python library for controlling STServos with GUI interface",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/waveshare_stservo_python",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": ["pytest>=6.0", "pytest-cov", "black", "flake8"],
        "gui": ["tkinter"],
    },
    entry_points={
        "console_scripts": [
            "stservo-gui=stservo.gui.servo_gui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "stservo": ["../config/*.yaml"],
    },
)
