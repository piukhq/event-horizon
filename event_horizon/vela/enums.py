from enum import Enum


class PendingRewardChoices(str, Enum):
    TRANSFER = "Transfer"
    CONVERT = "Convert"
    REMOVE = "Remove"

    @classmethod
    def get_choices(cls, allow_transfer: bool) -> list[str]:
        return [attr.value for attr in cls if attr != cls.TRANSFER or allow_transfer]

    def get_strategy(self) -> tuple[bool, bool]:
        match self:
            case PendingRewardChoices.TRANSFER:
                transfer, issue = True, False
            case PendingRewardChoices.CONVERT:
                transfer, issue = False, True
            case PendingRewardChoices.REMOVE:
                transfer, issue = False, False

        return transfer, issue
