Available Methods
=================

This page is about Pyrogram methods. All the methods listed here are bound to a :class:`~pyrogram.Client` instance,
except for :meth:`~pyrogram.idle()` and :meth:`~pyrogram.compose()`, which are special functions that can be found in
the main package directly.

.. code-block:: python

    from pyrogram import Client

    app = Client("my_account")

    with app:
        app.send_message("me", "hi")

-----

.. currentmodule:: pyrogram.Client

{sections}
.. currentmodule:: pyrogram

.. autosummary::
    :nosignatures:

    idle
    compose

.. toctree::
    :hidden:

    idle
    compose
