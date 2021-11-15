# bitpynda
[![Release](https://img.shields.io/github/release/S1SYPHOS/bitpynda.svg)](https://github.com/S1SYPHOS/bitpynda/releases) [![License](https://img.shields.io/github/license/S1SYPHOS/bitpynda.svg)](https://github.com/S1SYPHOS/bitpynda/blob/main/LICENSE) [![Issues](https://img.shields.io/github/issues/S1SYPHOS/bitpynda.svg)](https://github.com/S1SYPHOS/bitpynda/issues)

A simple Python library & CLI utility lending a hand with (tax) reports on your "Bitpanda" portfolio.

## Getting started

Running `setup.bash` will install all dependencies inside a virtual environment, ready for action:

```bash
# Set up & activate virtualenv
virtualenv -p python3 venv

# shellcheck disable=SC1091
source venv/bin/activate

# Install dependencies
python -m pip install --editable .
```


## Usage

Using this library is straightforward:

```text
$ bitpynda --help
Usage: bitpynda [OPTIONS] COMMAND [ARGS]...

  A simple CLI utility for reports on 'Bitpanda' portfolios

Options:
  -v, --verbose  Enable verbose mode
  --version      Show the version and exit.
  --help         Show this message and exit.

Commands:
  connect  Creates report using the 'Bitpanda' API
  report   Creates report using an exported CSV file
```


WIP

## Credits

This library started out as fork of [`Bitpanda-Report`](https://github.com/MrRo-de/Bitpanda-Report) by [MrRo-de](https://github.com/MrRo-de) and has been heavily rewritten since then. For the API implementation the Typescript package [`pandagainz`](https://github.com/igoramadas/pandagainz) by [Igor Ramadas](https://github.com/igoramadas) was ported to Python. Thanks for your great work, you guys are awesome!

**Happy coding!**
