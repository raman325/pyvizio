from setuptools import setup

with open('pyvizio/version.py') as f: exec(f.read())

setup(
    name='pyvizio',

    version=__version__,
    description='Python library for interfacing with Vizio SmartCast TV',
    url='https://github.com/sllh/pyviziocast',

    author='Vlad Korniev',
    author_email='vladimir.kornev@gmail.com',

    license='GPLv3',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
    ],

    keywords='vizio smartcast',

    packages=["pyvizio"],

    install_requires=['click', 'requests', 'jsonpickle', 'xmltodict'],
    entry_points={
        'console_scripts': [
            'pyvizio=pyvizio.cli:cli',
        ],
    },
)
