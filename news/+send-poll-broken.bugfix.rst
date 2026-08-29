``send_poll`` raised ``TypeError`` on every call since the layer-229 bump:
``raw.types.Poll`` gained a required ``hash`` field and the request did not pass
it. Parsing the reply then failed too -- ``Poll._parse`` built ``PollOption``
with seven fields it did not have, so any poll reaching the parser raised inside
the handler worker. ``PollOption`` now carries the full set (persistent id,
media, vote percentage, recent voters, who added the option and when).
