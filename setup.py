from setuptools import setup, find_packages

setup(
    name="cdata",
    version="0.0.1-dev",
    packages=find_packages(),

    # Metadata for PyPi
    author="Jonathan Heathcote",
    description="High-level C datastructure assembly library",
    license="GPLv2",

    # Requirements
    install_requires=["six", "enum34"],
    tests_require=["pytest>=2.6", "pytest-cov", "mock"],
)
