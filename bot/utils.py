from aiogram.utils.helper import Helper, HelperMode, ListItem


class PollStates(Helper):
    mode = HelperMode.snake_case

    STATE_0_DEFAULT = ListItem()
    STATE_1_ANSWER = ListItem()
    STATE_2_QUESTION = ListItem()
    STATE_3_ENDED = ListItem()
