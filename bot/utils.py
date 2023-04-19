from aiogram.utils.helper import Helper, HelperMode, ListItem


class PollStates(Helper):
    """
    Класс необходим для хранения состояний, при создании опроса. 0 - по умолчанию,
    1 - после добавления вопроса,
    2 - после добавления ответов, для завершения создания опроса.
    """
    mode = HelperMode.snake_case

    STATE_0_DEFAULT = ListItem()
    STATE_1_ANSWER = ListItem()
    STATE_2_QUESTION = ListItem()
