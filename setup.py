from setuptools import setup, find_packages

VERSION = "0.1.2"

NAME = "macq"

DESCRIPTION = "Action model acquisition from state trace data."

DEPENDENCIES = [
    "tarski",
    "requests",
    "rich",
    "nnf",
    "python-sat",
    "bauhaus",
    "numpy"
]

DEV_DEPENDENCIES = [
    "pytest",
    "pytest-cov",
    "flake8",
    "black",
    "pre-commit",
]

CLASSIFIERS = [
    "Intended Audience :: Science/Research",
    "Topic :: Scientific/Engineering",
    "Topic :: Scientific/Engineering :: Mathematics",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3 :: Only",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

with open("LICENSE", "r", encoding="utf-8") as f:
    LICENSE = f.read()

with open("README.md", "r", encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

setup(
    name=NAME,
    version=VERSION,
    author="Ethan Callanan, Rebecca De Venezia, Victoria Armstrong, Alison Parades, Tathagata Chakraborti, Christian Muise",
    author_email="christian.muise@queensu.ca",
    license="MIT",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    keywords="planning model acquisition trace",
    url="https://github.com/ai-planning/macq",
    classifiers=CLASSIFIERS,
    packages=find_packages("macq/macq"),
    python_requires=">=3.7",
    install_requires=DEPENDENCIES,
    extras_require={"dev": DEV_DEPENDENCIES},
)
