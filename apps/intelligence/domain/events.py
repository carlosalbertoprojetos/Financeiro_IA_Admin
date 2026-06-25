from enum import Enum


class TimelineEventType(str, Enum):
    """Canonical operational event types for the EOR timeline."""

    CARD_CREATED = "CARD_CREATED"
    CARD_MOVED = "CARD_MOVED"
    CARD_ASSIGNED = "CARD_ASSIGNED"
    CARD_UNASSIGNED = "CARD_UNASSIGNED"
    LABEL_ADDED = "LABEL_ADDED"
    LABEL_REMOVED = "LABEL_REMOVED"
    COMMENT_ADDED = "COMMENT_ADDED"
    CHECKLIST_STARTED = "CHECKLIST_STARTED"
    CHECKLIST_COMPLETED = "CHECKLIST_COMPLETED"
    CHECKLIST_ITEM_COMPLETED = "CHECKLIST_ITEM_COMPLETED"
    DUE_DATE_CHANGED = "DUE_DATE_CHANGED"
    CARD_COMPLETED = "CARD_COMPLETED"
    CARD_REOPENED = "CARD_REOPENED"
    ATTACHMENT_ADDED = "ATTACHMENT_ADDED"
    BLOCKER_REGISTERED = "BLOCKER_REGISTERED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(item.value, item.name.replace("_", " ").title()) for item in cls]


TRELLO_ACTION_MAP: dict[str, TimelineEventType] = {
    "createCard": TimelineEventType.CARD_CREATED,
    "copyCard": TimelineEventType.CARD_CREATED,
    "commentCard": TimelineEventType.COMMENT_ADDED,
    "addAttachmentToCard": TimelineEventType.ATTACHMENT_ADDED,
    "addLabelToCard": TimelineEventType.LABEL_ADDED,
    "removeLabelFromCard": TimelineEventType.LABEL_REMOVED,
    "addMemberToCard": TimelineEventType.CARD_ASSIGNED,
    "removeMemberFromCard": TimelineEventType.CARD_UNASSIGNED,
    "updateCheckItemStateOnCard": TimelineEventType.CHECKLIST_ITEM_COMPLETED,
    "createCheckItem": TimelineEventType.CHECKLIST_STARTED,
}
