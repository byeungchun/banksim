"""
Inter-bank loan agent
"""

from mesa import Agent


class Ibloan(Agent):

    def __init__(self, params):
        super().__init__(params.get("unique_id"), params.get("model"))
        self.ib_rate = params.get("libor_rate")
        self.ib_amount = 0
        self.ib_last_color = None  # used to create visual effects
        self.ib_creditor = None
        self.ib_debtor = None

    @property
    def ib_rate(self):
        return self.__ib_rate

    @ib_rate.setter
    def ib_rate(self, ib_rate):
        self.__ib_rate = ib_rate

    @property
    def ib_amount(self):
        return self.__ib_amount

    @ib_amount.setter
    def ib_amount(self, ib_amount):
        self.__ib_amount = ib_amount

    @property
    def ib_creditor(self):
        return self.__ib_creditor

    @ib_creditor.setter
    def ib_creditor(self, ib_creditor):
        self.__ib_creditor = ib_creditor

    @property
    def ib_debtor(self):
        return self.__ib_debtor

    @ib_debtor.setter
    def ib_debtor(self, ib_debtor):
        self.__ib_debtor = ib_debtor

    def get_all_variables(self):
        res = [
            '',  # AgtSaverId
            '',  # SimId
            '',  # StepCnt
            self.unique_id,
            self.ib_rate,
            self.ib_amount,
            self.ib_creditor.unique_id,
            self.ib_debtor.unique_id,
            '' # datetime
        ]
        return res
