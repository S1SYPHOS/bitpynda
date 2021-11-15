import setuptools

# Load README
with open('README.md', 'r', encoding='utf8') as file:
    long_description = file.read()

# Define package metadata
setuptools.setup(
    name='bitpynda',
    version='0.1.0',
    author='Martin Folkers',
    author_email='hello@twobrain.io',
    description='A simple Python library & CLI utility lending a hand with tax reports on your "Bitpanda" portfolio',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/S1SYPHOS/bitpynda',
    license='MIT',
    project_urls={
        'Issues': 'https://github.com/S1SYPHOS/bitpynda/issues',
    },
    entry_points='''
        [console_scripts]
        bitpynda=src.cli:cli
    ''',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=setuptools.find_packages(),
    install_requires=[
        'click',
        'httpx',
        'fpdf2',
        'matplotlib',
        'pandas',
        'pypng',
        'pyqrcode',
        'pyyaml',
    ],
    python_requires='>=3.7',
)
