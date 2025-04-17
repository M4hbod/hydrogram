#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Hydrogram <https://hydrogram.org>
#
#  This file is part of Hydrogram.
#
#  Hydrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Hydrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Hydrogram.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import re
from importlib import import_module
from typing import ClassVar

from .exceptions.all import exceptions
from .exceptions.bad_request_400 import BadRequest
from .exceptions.flood_420 import Flood
from .exceptions.forbidden_403 import Forbidden
from .exceptions.internal_server_error_500 import InternalServerError
from .exceptions.not_acceptable_406 import NotAcceptable
from .exceptions.see_other_303 import SeeOther
from .exceptions.service_unavailable_503 import ServiceUnavailable
from .exceptions.unauthorized_401 import Unauthorized
from .pyromod import ListenerStopped, ListenerTimeout
from .rpc_error import RPCError, UnknownError


class BadMsgNotification(Exception):  # noqa: N818
    descriptions: ClassVar = {
        16: "The msg_id is too low, the client time has to be synchronized.",
        17: "The msg_id is too high, the client time has to be synchronized.",
        18: "Incorrect two lower order of the msg_id bits, the server expects the client message "
        "msg_id to be divisible by 4.",
        19: "The container msg_id is the same as the msg_id of a previously received message.",
        20: "The message is too old, it cannot be verified by the server.",
        32: "The msg_seqno is too low.",
        33: "The msg_seqno is too high.",
        34: "An even msg_seqno was expected, but an odd one was received.",
        35: "An odd msg_seqno was expected, but an even one was received.",
        48: "Incorrect server salt.",
        64: "Invalid container.",
    }

    def __init__(self, code):
        description = self.descriptions.get(code, "Unknown error code")
        super().__init__(f"[{code}] {description}")


class SecurityError(Exception):
    """Generic security error."""

    @classmethod
    def check(cls, cond: bool, msg: str):
        """Raises this exception if the condition is false"""
        if not cond:
            raise cls(f"Check failed: {msg}")


class SecurityCheckMismatch(SecurityError):  # noqa: N818
    """Raised when a security check mismatch occurs."""

    def __init__(self, msg: str | None = None):
        super().__init__("A security check mismatch has occurred." if msg is None else msg)


class CDNFileHashMismatch(SecurityError):  # noqa: N818
    """Raised when a CDN file hash mismatch occurs."""

    def __init__(self, msg: str | None = None):
        super().__init__("A CDN file hash mismatch has occurred." if msg is None else msg)


error_objects = {}
for error_code, error_dict in exceptions.items():
    for error_name, class_name in error_dict.items():
        if error_name == "_":
            continue
        base = re.sub(r"(?<!^)(?=[A-Z])", "_", error_dict["_"]).lower()
        module_name = f".exceptions.{base}_{error_code}"
        try:
            module = import_module(module_name, package="hydrogram.errors")
            error_objects[class_name] = getattr(module, class_name)
        except (ImportError, AttributeError):
            continue

locals().update(error_objects)

__all__ = [
    "BadMsgNotification",
    "BadRequest",
    "CDNFileHashMismatch",
    "Flood",
    "Forbidden",
    "InternalServerError",
    "ListenerStopped",
    "ListenerTimeout",
    "NotAcceptable",
    "RPCError",
    "SecurityCheckMismatch",
    "SecurityError",
    "SeeOther",
    "ServiceUnavailable",
    "Unauthorized",
    "UnknownError",
]
__all__ += list(error_objects.keys())  # type: ignore
