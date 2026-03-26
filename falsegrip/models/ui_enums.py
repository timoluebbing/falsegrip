"""UI Enums and Constants."""

from enum import Enum


class EditorMode(str, Enum):
    """Modes for the workout editor dialog."""

    CREATE = "create"
    EDIT = "edit"
    FROM_PLAN = "create_from_plan"
