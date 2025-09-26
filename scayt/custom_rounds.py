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

rounds = DotDict({"western_20": western_20})
