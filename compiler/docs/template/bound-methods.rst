Bound Methods
=============

Some Pyrogram types define what are called bound methods. Bound methods are functions attached to a type which are
accessed via an instance of that type. They make it even easier to call specific methods by automatically inferring
some of the required arguments.

.. code-block:: python

    from pyrogram import Client

    app = Client("my_account")


    @app.on_message()
    def hello(client, message)
        message.reply("hi")


    app.run()

-----

.. currentmodule:: pyrogram.types

{sections}
