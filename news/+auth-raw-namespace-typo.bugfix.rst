``Auth.create()`` referenced ``raw.pyrogram.ClientDHInnerData``, which does not exist (the
constructor lives at ``raw.types.ClientDHInnerData``) -- a leftover from the whole-tree
``hydrogram`` -> ``pyrogram`` rename. Every DH key exchange failed, so no session could ever
authenticate for the first time; a pre-existing session file masked it. Fixed, and
``tests/contract/test_raw_references.py`` now flags any ``raw.<namespace>.*`` reference whose
namespace isn't one of ``types``/``functions``/``base``/``core``, which this typo did not trip
before (its fixed namespace list only checked references it already recognized).
