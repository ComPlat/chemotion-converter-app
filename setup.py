import re

from setuptools import find_packages, setup

with open('converter_app/__init__.py') as f:
    metadata = dict(re.findall(r'__(.*)__ = [\']([^\']*)[\']', f.read()))

with open('requirements/default.txt') as f:
    install_requires = f.readlines()

with open('requirements/common.txt') as f:
    install_requires += f.readlines()[1:]

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
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)'
    ],
    packages=find_packages(),
    include_package_data=True
)
