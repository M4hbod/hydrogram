Available Types
===============

This page is about Pyrogram Types. All types listed here are available through the ``pyrogram.types`` package.
Unless required as argument to a client method, most of the types don't need to be manually instantiated because they
are only returned by other methods. You also don't need to import them, unless you want to type-hint your variables.

.. code-block:: python

    from pyrogram.types import User, Message, ...

.. note::

    Optional fields always exist inside the object, but they could be empty and contain the value of ``None``.
    Empty fields aren't shown when, for example, using ``print(message)`` and this means that
    ``hasattr(message, "photo")`` always returns ``True``.

    To tell whether a field is set or not, do a simple boolean check: ``if message.photo: ...``.

-----

.. currentmodule:: pyrogram.types

{sections}
