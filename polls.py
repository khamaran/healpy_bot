from typing import List

from aiogram.dispatcher.filters.state import StatesGroup


class PollState(StatesGroup):
    type: str = "regular"

    def __init__(self, poll_id, question, options, owner_id):
        self.poll_id: str = poll_id
        self.question: str = question
        self.options: List[str] = [*options]
        self.owner: int = owner_id
        self.chat_id: int = 0
        self.message_id: int = 0
