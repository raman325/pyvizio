from setuptools import setup
from pyvizio.version import __version__

with open("pyvizio/version.py") as f:
    exec(f.read())
with open("README.md", "r") as myfile:
    longdescription = myfile.read()

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
    packages=["pyvizio"],
    install_requires=[
        "aiohttp",
        "asyncio",
        "click",
        "requests",
        "jsonpickle",
        "xmltodict",
    ],
    entry_points={"console_scripts": ["pyvizio=pyvizio.cli:cli"]},
)
