from setuptools import setup, find_packages


setup(
    name='pypofatu',
    version='1.3.0',
    license='Apache 2.0',
    description='programmatic access to pofatu-data',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    author='Robert Forkel',
    author_email='forkel@shh.mpg.de',
    url='',
    keywords='data',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    python_requires='>=3.5',
    install_requires=[
        'pybtex<0.23; python_version < "3.6"',
        'pybtex; python_version > "3.5"',
        'attrs>=19.3',
        'xlrd',
        'clldutils>=3.5',
        'tqdm',
    ],
    extras_require={
        'dev': ['flake8', 'wheel', 'twine'],
        'test': [
            'mock',
            'pytest>=5',
            'pytest-mock',
            'pytest-cov',
            'coverage>=4.2',
        ],
    },
    entry_points={
        'console_scripts': [
            'pofatu=pypofatu.__main__:main',
        ]
    },
)

