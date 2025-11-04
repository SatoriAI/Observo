from enum import IntEnum, StrEnum


class OutlineAction(IntEnum):
    SEND_TO_OWNER = 0
    SEND_TO_CLIENT = 1


class Workflows(StrEnum):
    OUTLINE_PREPARER = "Prepare Outlines for Matched Grants"
    AI_CHECK = "AI Check"
