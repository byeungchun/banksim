from mesa import Agent

class Saver(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.balance  # deposit balance with bank
        self.withdraw_prob  # probability of withdrawing deposit and shift to other bank
        self.exit_prob  # probability that saver withdraws and exits banking system
        self.bank_id  # identity of saver's bank
        self.region_id  # regionof saver
        self.owns_account  # owns account with bank-id
        self.saver_solvent  # solvent if bank returns principal, may become insolvent if bank is bankrupt
        self.saver_exit  # saver exits the banking system?
        self.saver_current  # old saver/ if false, it is a new entrant to the system
        self.saver_last_color  # used to create visual effects