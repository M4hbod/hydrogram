from .apply_boost import ApplyBoost
from .get_boosts import GetBoosts
from .get_boosts_status import GetBoostsStatus


class Premium(
    ApplyBoost,
    GetBoosts,
    GetBoostsStatus,
):
    pass
