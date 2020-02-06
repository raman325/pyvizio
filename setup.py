from setuptools import find_packages, setup

with open("pyvizio/version.py") as f:
    exec(f.read())
with open("README.md", "r") as myfile:
    longdescription = myfile.read()

PACKAGES = find_packages(exclude=["tests", "tests.*"])

setup(
    name="pyvizio",
    version=__version__,
    description="Python library for interfacing with Vizio SmartCast TVs and Sound Bars (2016+ models)",
    long_description=longdescription,
    long_description_content_type="text/markdown",
    url="https://github.com/vkorn/pyvizio",
    author="Vlad Korniev",
    author_email="vladimir.kornev@gmail.com",
    license="GPLv3",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
    ],
    keywords="vizio smartcast",
    packages=PACKAGES,
    install_requires=[
        "aiohttp",
        "click",
        "jsonpickle",
        "requests",
        "tabulate",
        "xmltodict",
        "zeroconf",
    ],
    entry_points={"console_scripts": ["pyvizio=pyvizio.cli:cli"]},
)
