``types.Location`` accepts ``client``. Two inline-query parsers passed it and
raised ``TypeError``, which meant an inline query carrying a location never
reached its handler.
