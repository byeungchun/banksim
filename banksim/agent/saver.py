"""
Saver agent
"""

from mesa import Agent
from numpy.random import uniform


class Saver(Agent):

    def __init__(self, params):
        super().__init__(params.get("unique_id"), params.get("model"))
        # deposit balance with bank
        self.balance = params.get("balance")
        # owns account with bank-id
        self.owns_account = params.get("own_account")
        # solvent if bank returns principal, may become insolvent if bank is bankrupt
        self.saver_solvent = params.get("saver_solvent")
        # probability of withdrawing deposit and shift to other bank
        self.withdraw_prob = uniform(high=params.get("withdraw_upperbound"))
        # probability that saver withdraws and exits banking system
        self.exit_prob = uniform(high=params.get("exitprob_upperbound"))
        # saver exits the banking system?
        self.saver_exit = params.get("saver_exit")
        # old saver/ if false, it is a new entrant to the system
        self.saver_current = None
        # identity of saver's bank
        self.bank_id = None
        # region of saver
        self.region_id = None
        self.saver_last_color = None

    @property
    def balance(self):
        return self.__balance

    @balance.setter
    def balance(self, balance):
        self.__balance = balance

    @property
    def owns_account(self):
        return self.__owns_account

    @owns_account.setter
    def owns_account(self, owns_account):
        self.__owns_account = owns_account

    @property
    def saver_solvent(self):
        return self.__saver_solvent

    @saver_solvent.setter
    def saver_solvent(self, saver_solvent):
        self.__saver_solvent = saver_solvent

    @property
    def withdraw_prob(self):
        return self.__withdraw_prob

    @withdraw_prob.setter
    def withdraw_prob(self, withdraw_prob):
        self.__withdraw_prob = withdraw_prob

    @property
    def exit_prob(self):
        return self.__exit_prob

    @exit_prob.setter
    def exit_prob(self, exit_prob):
        self.__exit_prob = exit_prob

    @property
    def saver_exit(self):
        return self.__saver_exit

    @saver_exit.setter
    def saver_exit(self, saver_exit):
        self.__saver_exit = saver_exit

    @property
    def bank_id(self):
        return self.__bank_id

    @bank_id.setter
    def bank_id(self, bank_id):
        self.__bank_id = bank_id

    @property
    def region_id(self):
        return self.__region_id

    @region_id.setter
    def region_id(self, region_id):
        self.__region_id = region_id

    def get_all_variables(self):
        res = [
            '',  # AgtSaverId
            '',  # SimId
            '',  # StepCnt
            self.unique_id,
            self.balance,
            self.withdraw_prob,
            self.exit_prob,
            self.bank_id,
            self.region_id,
            self.owns_account if self.owns_account is None else int(self.owns_account),
            self.saver_solvent if self.saver_solvent is None else int(self.saver_solvent),
            self.saver_exit if self.saver_exit is None else int(self.saver_exit),
            self.saver_current if self.saver_current is None else int(self.saver_current),
            ''  # Datetime
        ]
        return res
