from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

setup(
	name='gcapi-python',
	version='0.0.9',
	author='Kyu Mok (Ricky) Kim',
	author_email='rickykim93@hotmail.com',
	url='https://github.com/rickykim93/gcapi-python',
	description='Unofficial Python library for Gain Capital API from Forex.com',
	long_description=open(path.join(here, 'README.md'), encoding='utf-8').read(),
	long_description_content_type="text/markdown",
	packages=find_packages(),
	include_package_data=True,
	install_requires=[
		'requests>=2.22.0',
		'pandas>=0.23.4',
		'lightstreamer-client>=0.1'
	],
	test_suite='tests',
)