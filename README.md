<p align="center">
    <a href="https://github.com/pyrogram/pyrogram">
        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/pyrogram/pyrogram/main/docs/source/_static/pyrogram-dark.png">
            <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/pyrogram/pyrogram/main/docs/source/_static/pyrogram-light.png">
            <img alt="Pyrogram" width="128" src="https://raw.githubusercontent.com/pyrogram/pyrogram/main/docs/source/_static/pyrogram-light.png">
        </picture>
    </a>
    <br>
    <b>Python Framework for the Telegram MTProto API</b>
    <br>
    <a href="https://pyrogram.org">
        Homepage
    </a>
    •
    <a href="https://docs.pyrogram.org">
        Documentation
    </a>
    •
    <a href="https://docs.pyrogram.org/en/latest/releases.html">
        Releases
    </a>
    •
    <a href="https://t.me/PyrogramNews">
        News
    </a>
</p>

# Pyrogram

[![We use Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI package version](https://img.shields.io/pypi/v/pyrogram.svg)](https://pypi.python.org/pypi/pyrogram)
[![PyPI license](https://img.shields.io/pypi/l/pyrogram.svg)](https://pypi.python.org/pypi/pyrogram)
[![PyPI python versions](https://img.shields.io/pypi/pyversions/pyrogram.svg)](https://pypi.python.org/pypi/pyrogram)
[![PyPI download month](https://img.shields.io/pypi/dm/pyrogram.svg)](https://pypi.python.org/pypi/pyrogram/)
[![GitHub Actions status](https://github.com/pyrogram/pyrogram/actions/workflows/python.yml/badge.svg)](https://github.com/pyrogram/pyrogram/actions)

## Description

Pyrogram is a Python library for interacting with the Telegram MTProto API. It provides a simple and intuitive interface for developers to leverage the power of Telegram's API in their Python applications.

## Installation

To install Pyrogram, you need Python 3 installed on your system. If you don't have Python installed, you can download it from the official website.

To install Pyrogram, use pip:

```bash
pip install pyrogram -U
```

## Usage

Here is a basic example of how to use Pyrogram:

```python
from pyrogram import Client, filters

app = Client("my_account")


@app.on_message(filters.private)
async def hello(client, message):
    await message.reply("Hello from Pyrogram!")


app.run()
```

## Features

- **Easy to use:** Pyrogram provides a simple and intuitive interface for developers to leverage the power of Telegram's API in their Python applications, while still allowing advanced usages.
- **Elegant:** Low-level details are abstracted and re-presented in a more convenient way, making the Telegram API more accessible.
- **Fast:** Pyrogram is boosted by [TgCrypto](https://github.com/pyrogram/tgcrypto), a high-performance cryptography library written in C, which makes it faster than other Python Telegram libraries.
- **Type-hinted:** Types and methods are all type-hinted, enabling excellent editor support and making it easier to write and maintain code.
- **Async:** Pyrogram is fully asynchronous, which means it can handle multiple requests at the same time, making it faster and more efficient.
- **Powerful:** Pyrogram provides full access to Telegram's API to execute any official client action and more, giving developers the flexibility to build powerful applications.

## Resources

- The [documentation](https://docs.pyrogram.org) is the technical reference for Pyrogram. It includes detailed usage guides, API reference, and more.
- The [homepage](https://pyrogram.org) is the official website for Pyrogram. It includes a quickstart guide, a list of features, and more.
- Our [Telegram channel](https://t.me/PyrogramNews) is where we post news and updates about Pyrogram.

## Contributing

Pyrogram is an open source project and we welcome contributions from the community. We appreciate all types of contributions, including bug reports, feature requests, documentation improvements, and code contributions.

To get started, please review our [Contribution Guidelines](https://github.com/pyrogram/pyrogram/blob/main/CONTRIBUTING.md) for more information.

All contributors are expected to adhere to the [Code of Conduct](https://github.com/pyrogram/.github/blob/main/CODE_OF_CONDUCT.md). Please read it before contributing.

We appreciate your help in making Pyrogram better!

## Support

Pyrogram is an open source project. Your support helps us maintain and improve the library. You can support the development of Pyrogram through the following platforms:

- [Liberapay](https://liberapay.com/pyrogram)
- [OpenCollective](https://opencollective.com/pyrogram)

## Thanks

- [Pyrogram](https://github.com/pyrogram/pyrogram) and its contributors for the inspiration and base code.

## License

You may copy, distribute and modify the software provided that modifications are described and licensed for free under [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html). Derivatives works (including modifications or anything statically linked to the library) can only be redistributed under LGPL-3, but applications that use the library don't have to be.
