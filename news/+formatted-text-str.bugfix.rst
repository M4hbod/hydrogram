``types.FormattedText(text=...)`` accepts a plain ``str``. It was annotated
``Str`` -- the ``str`` subclass the parser hands back -- which no caller passes.
