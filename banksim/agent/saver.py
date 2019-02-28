import numpy as np
from mesa import Agent


class Saver(Agent):

    balance = None  # deposit balance with bank
    withdraw_prob = None  # probability of withdrawing deposit and shift to other bank
    exit_prob = None  # probability that saver withdraws and exits banking system
    bank_id = None  # identity of saver's bank
    region_id = None  # region of saver
    owns_account = None  # owns account with bank-id
    saver_solvent = None  # solvent if bank returns principal, may become insolvent if bank is bankrupt
    saver_exit = None  # saver exits the banking system?
    saver_current = None  # old saver/ if false, it is a new entrant to the system
    saver_last_color = None  # used to create visual effects

    def __init__(self, unique_id, model, balance=1, owns_account=False, saver_solvent=True, saver_exit=False,
                 saver_last_color='black'):
        super().__init__(unique_id, model)
        self.balance = balance
        self.owns_account = owns_account
        self.saver_solvent = saver_solvent
        self.withdraw_prob = np.random.randint(0, 21) / 100.0
        self.exit_prob = np.random.randint(0, 6) / 100.0
        self.saver_exit = saver_exit
        self.saver_last_color = saver_last_color

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
            '' # Datetime
        ]
        return res
