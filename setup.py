# coding=utf-8
import codecs
import re
from os import path
from setuptools import setup, find_packages


def read(*parts):
    file_path = path.join(path.dirname(__file__), *parts)
    return codecs.open(file_path, encoding='utf-8').read()


def find_version(*parts):
    version_file = read(*parts)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='academic-integrations',
    version=find_version('odoo', '__init__.py'),
    description='Un sistema de integraciones para edoo académico.'
                '\n- Extensión de odoo (sistema contable)',
    long_description=read('README.rst'),
    author='Oscar Gil',
    author_email='info@edoo.io',
    url='https://github.com/oscaresgil/academic-integrations',
    packages=find_packages(),
    install_requires=[],
)