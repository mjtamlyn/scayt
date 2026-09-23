from archeryutils.load_rounds import DotDict
from archeryutils.rounds import Pass, Round

western_20 = Round(
    "Western 20",
    [
        Pass.at_target(
            48,
            "5_zone",
            (122, "cm"),
            (20, "yard"),
        ),
        Pass.at_target(
            48,
            "5_zone",
            (122, "cm"),
            (10, "yard"),
        ),
    ],
    codename="western_20",
    location="outdoor",
    body="AGB",
    family="western",
)

long_metric_vi = Round(
    "Long Metric VI",
    [
        Pass.at_target(
            36,
            "10_zone",
            (122, "cm"),
            (20, "metre"),
        ),
        Pass.at_target(
            36,
            "10_zone",
            (122, "cm"),
            (10, "metre"),
        ),
    ],
    codename="long_metric_vi",
    location="outdoor",
    body="AGB",
    family="long_metric",
)

rounds = DotDict({
    "western_20": western_20,
    "long_metric_vi": long_metric_vi,
})
