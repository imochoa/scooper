#!/usr/bin/env python3
# Copyright Spanflug Technologies GmbH

from distutils.core import setup
import os

REPO_DIR = os.path.dirname(__file__)
with open(os.path.join(REPO_DIR, 'requirements.txt'), 'r') as f:
    requirements = f.read().splitlines()

scripts = [os.path.join('bin', s) for s in os.listdir(os.path.join(REPO_DIR, 'bin'))]

with open(os.path.join(REPO_DIR, 'README.md'), 'r') as f:
    long_description = f.read().splitlines()

setup(
    name='scooper',
    version='1.0.0',
    packages=['pyscooper',
        ],
    scripts=scripts,
    license='MIT',
    install_requires=requirements
)
