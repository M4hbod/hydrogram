Install Guide
=============

Being a modern Python framework, Pyrogram requires an up to date version of Python to be installed in your system.
We recommend using the latest versions of both Python 3 and pip.

-----

Install Pyrogram
-----------------

-   The easiest way to install and upgrade Pyrogram to its latest stable version is by using **pip**:

    .. code-block:: text

        $ pip3 install -U pyrogram

-   or, with :doc:`TgCrypto and uvloop <../topics/speedups>` as extra requirements (recommended for better performance):

    .. code-block:: text

        $ pip3 install -U "pyrogram[fast]"

Bleeding Edge
-------------

The development version from the git ``dev`` branch contains the latest features and fixes, but it
may also include unfinished changes, bugs, or unstable code. Using this version can lead to unexpected
behavior, or compatibility issues. It is recommended only for advanced users who want to
test new features and are comfortable troubleshooting problems.

You can install the development version using this command:

.. code-block:: text

    $ pip3 install -U https://github.com/pyrogram/pyrogram/archive/dev.zip

Verifying
---------

To verify that Pyrogram is correctly installed, open a Python shell and import it.
If no error shows up you are good to go.

.. parsed-literal::

    >>> import pyrogram
    >>> pyrogram.__version__
    'x.y.z'

.. _`Github repo`: http://github.com/pyrogram/pyrogram
