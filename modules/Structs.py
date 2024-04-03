from enum import Enum

class ProcessorType(Enum):
    PROMPT = "PROMPT"
    PROMPT_IMAGE = "PROMPT_IMAGE"
    PROMPT_POE_CREW = "PROMPT_POE_CREW"
    PROMPT_RECEIPT_CREW = "PROMPT_RECEIPT_CREW"
    PROMPT_INVESTMENT_CREW = "PROMPT_INVESTMENT_CREW"
    PROMPT_BET_TENNIS_CREW = "PROMPT_BET_TENNIS_CREW"

class StatusType(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    WAITING = "WAITING"
    COLLECTED = "COLLECTED"

class RowType(Enum):
    ONE = "ONE"
    ALL = "ALL"

Task = {
    "id": "",
    "prompt": "",
    "processor": ProcessorType.PROMPT.value,
    "webhook": "",
    "answer": "",
    "status": StatusType.SUCCESS.value,
    "updated_at": "",
    "created_at": ""
}