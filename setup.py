import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

from setuptools import find_packages, setup

with open(BASE_DIR / 'converter_app/__init__.py') as f:
    metadata = dict(re.findall(r'__(.*)__ = [\']([^\']*)[\']', f.read()))

with open(BASE_DIR / 'requirements/common.txt') as f:
    install_requires = f.readlines()

setup(
    name=metadata['title'],
    version=metadata['version'],
    author=metadata['author'],
    author_email=metadata['email'],
    maintainer=metadata['author'],
    maintainer_email=metadata['email'],
    license=metadata['license'],
    url='https://github.com/ComPlat/converter-app',
    description=u'',
    long_description=open('README.md').read(),
    install_requires=install_requires,
    classifiers=[
        # https://pypi.org/classifiers/
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)'
    ],
    packages=find_packages(),
    include_package_data=True
)
