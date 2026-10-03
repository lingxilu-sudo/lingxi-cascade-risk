"""Setup configuration for cascade_risk package."""

from setuptools import setup, find_packages

setup(
    name="cascade-risk",
    version="2.0.0",
    description="Physics-based Monte Carlo model for space debris insurance pricing",
    author="Lingxi Lu",
    author_email="ling.xi.lu@gmail.com",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.20.0",
        "matplotlib>=3.4.0",
        "scipy>=1.7.0",
        "pyyaml>=5.4",
    ],
    extras_require={
        "dev": ["pytest>=7.0"],
    },
    entry_points={
        "console_scripts": [
            "cascade-risk=main:main",
        ],
    },
)
