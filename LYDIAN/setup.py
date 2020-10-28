#!/usr/bin/env python

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

version = {}
with open("lydian/__init__.py") as fp:
    exec(fp.read(), version)


setuptools.setup(
    name="lydian",
    version=version['__version__'],
    author="Vipin Sharma, Pradeep Singh, Spiro Kourtessis, Gavin Chang",
    author_email="sharmavipin@vmware.com",
    description="Tool for Traffic Generation, Management and Monitoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gitvipin/validation-app-engine",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
)
