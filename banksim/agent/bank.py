"""
Bank Agent
"""

from mesa import Agent


class Bank(Agent):

    def __init__(self, params):
        super().__init__(params.get("unique_id"), params.get("model"))
        self.equity = params.get("equity")
        self.bank_deposits = 0
        self.bank_loans = 0
        self.bank_reserves = 0 #equity + deposit
        self.rdeposits = params.get("rfree")  # assumes deposits are risk free
        self.bank_solvent = True
        self.defaulted_loans = 0
        self.bank_capitalized = True
        self.bank_dividend = 0
        self.bank_cum_dividend = 0
        self.upper_bound_cratio = 1.5 * params.get("car")  # set upper bound for capital ratio. set it to large number
        self.buffer_reserves_ratio = params.get("buffer_reserves_ratio")  # desired buffer or markup over
        self.credit_failure = False
        self.liquidity_failure = False
        self.ib_credits = 0
        self.ib_debits = 0
        self.total_assets = None  # bank_loans + bank_reserves
        self.bank_provisions = None  # provisions against expected losses
        self.bank_new_provisions = None  # required provisions, not met if bank defaults
        self.net_interest_income = 0
        self.interest_income = 0
        self.interest_expense = 0
        self.ib_interest_income = None
        self.ib_interest_expense = None
        self.ib_net_interest_income = None
        self.ib_credit_loss = None  # credit losses, interbank exposures
        self.capital_ratio = None  # capital to risk_weighted assets
        self.reserves_ratio = None  # reserves to deposits
        self.rwassets = None  # risk_weighted assets
        self.leverage_ratio = None  # leverage ratio = equity / total_assets
        self.deposit_outflow = 0
        self.deposit_inflow = 0
        self.net_deposit_flow = 0
        self.assets_liabilities = None
        self.ib_credits_4log = 0
        self.ib_debits_4log = 0
        self.ib_interest_income_4log = 0
        self.ib_interest_expense_4log = 0
        self.ib_net_interest_income_4log = 0
        self.ib_credit_loss_4log = 0

    def calculate_total_assets(self):
        self.total_assets = self.bank_reserves + self.bank_loans

    def calculate_leverage_ratio(self):
        self.leverage_ratio = self.equity / self.total_assets if self.total_assets !=0 else 0

    def calculate_capital_ratio(self):
        self.capital_ratio = self.equity / self.rwassets if self.rwassets !=0 else 0

    def calculate_reserve_ratio(self):
        self.reserves_ratio = self.bank_reserves / self.bank_deposits if self.bank_deposits !=0 else 0

    def calculate_reserve(self):
        self.bank_reserves = self.bank_reserves + self.net_deposit_flow

    def calculate_bank_deposits(self):
        self.bank_deposits = self.bank_deposits + self.net_deposit_flow

    def initialize_ib_variables(self):

        self.ib_credits_4log = self.ib_credits
        self.ib_debits_4log = self.ib_debits
        self.ib_interest_income_4log = self.ib_interest_income
        self.ib_interest_expense_4log = self.ib_interest_expense
        self.ib_net_interest_income_4log = self.ib_net_interest_income
        self.ib_credit_loss_4log = self.ib_credit_loss

        self.ib_credits = 0
        self.ib_debits = 0
        self.ib_interest_income = 0
        self.ib_interest_expense = 0
        self.ib_net_interest_income = 0
        self.ib_credit_loss = 0

    @property
    def equity(self):
        return self.__equity

    @equity.setter
    def equity(self, equity):
        self.__equity = equity

    @property
    def bank_deposits(self):
        return self.__bank_deposits

    @bank_deposits.setter
    def bank_deposits(self, bank_deposits):
        self.__bank_deposits = bank_deposits

    @property
    def bank_loans(self):
        return self.__bank_loans

    @bank_loans.setter
    def bank_loans(self, bank_loans):
        self.__bank_loans = bank_loans

    @property
    def bank_reserves(self):
        return self.__bank_reserves

    @bank_reserves.setter
    def bank_reserves(self, bank_reserves):
        self.__bank_reserves = bank_reserves

    @property
    def total_assets(self):
        return self.__total_assets

    @total_assets.setter
    def total_assets(self, total_assets):
        self.__total_assets = total_assets

    @property
    def bank_provisions(self):
        return self.__bank_provisions

    @bank_provisions.setter
    def bank_provisions(self, bank_provisions):
        self.__bank_provisions = bank_provisions

    @property
    def bank_new_provisions(self):
        return self.__bank_new_provisions

    @bank_new_provisions.setter
    def bank_new_provisions(self, bank_new_provisions):
        self.__bank_new_provisions = bank_new_provisions

    @property
    def rdeposits(self):
        return self.__rdeposits

    @rdeposits.setter
    def rdeposits(self, rdeposits):
        self.__rdeposits = rdeposits

    @property
    def ib_credits(self):
        return self.__ib_credits

    @ib_credits.setter
    def ib_credits(self, ib_credits):
        self.__ib_credits = ib_credits

    @property
    def ib_debits(self):
        return self.__ib_debits

    @ib_debits.setter
    def ib_debits(self, ib_debits):
        self.__ib_debits = ib_debits

    @property
    def net_interest_income(self):
        return self.__net_interest_income

    @net_interest_income.setter
    def net_interest_income(self, net_interest_income):
        self.__net_interest_income = net_interest_income

    @property
    def interest_income(self):
        return self.__interest_income

    @interest_income.setter
    def interest_income(self, interest_income):
        self.__interest_income = interest_income

    @property
    def interest_expense(self):
        return self.__interest_expense

    @interest_expense.setter
    def interest_expense(self, interest_expense):
        self.__interest_expense = interest_expense

    @property
    def ib_interest_income(self):
        return self.__ib_interest_income

    @ib_interest_income.setter
    def ib_interest_income(self, ib_interest_income):
        self.__ib_interest_income = ib_interest_income

    @property
    def ib_interest_expense(self):
        return self.__ib_interest_expense

    @ib_interest_expense.setter
    def ib_interest_expense(self, ib_interest_expense):
        self.__ib_interest_expense = ib_interest_expense

    @property
    def ib_net_interest_income(self):
        return self.__ib_net_interest_income

    @ib_net_interest_income.setter
    def ib_net_interest_income(self, ib_net_interest_income):
        self.__ib_net_interest_income = ib_net_interest_income

    @property
    def ib_credit_loss(self):
        return self.__ib_credit_loss

    @ib_credit_loss.setter
    def ib_credit_loss(self, ib_credit_loss):
        self.__ib_credit_loss = ib_credit_loss

    @property
    def capital_ratio(self):
        return self.__capital_ratio

    @capital_ratio.setter
    def capital_ratio(self, capital_ratio):
        self.__capital_ratio = capital_ratio

    @property
    def reserves_ratio(self):
        return self.__reserves_ratio

    @reserves_ratio.setter
    def reserves_ratio(self, reserves_ratio):
        self.__reserves_ratio = reserves_ratio

    @property
    def rwassets(self):
        return self.__rwassets

    @rwassets.setter
    def rwassets(self, rwassets):
        self.__rwassets = rwassets

    @property
    def leverage_ratio(self):
        return self.__leverage_ratio

    @leverage_ratio.setter
    def leverage_ratio(self, leverage_ratio):
        self.__leverage_ratio = leverage_ratio

    @property
    def bank_dividend(self):
        return self.__bank_dividend

    @bank_dividend.setter
    def bank_dividend(self, bank_dividend):
        self.__bank_dividend = bank_dividend

    @property
    def bank_cum_dividend(self):
        return self.__bank_cum_dividend

    @bank_cum_dividend.setter
    def bank_cum_dividend(self, bank_cum_dividend):
        self.__bank_cum_dividend = bank_cum_dividend

    @property
    def upper_bound_cratio(self):
        return self.__upper_bound_cratio

    @upper_bound_cratio.setter
    def upper_bound_cratio(self, upper_bound_cratio):
        self.__upper_bound_cratio = upper_bound_cratio

    @property
    def buffer_reserves_ratio(self):
        return self.__buffer_reserves_ratio

    @buffer_reserves_ratio.setter
    def buffer_reserves_ratio(self, buffer_reserves_ratio):
        self.__buffer_reserves_ratio = buffer_reserves_ratio

    @property
    def deposit_outflow(self):
        return self.__deposit_outflow

    @deposit_outflow.setter
    def deposit_outflow(self, deposit_outflow):
        self.__deposit_outflow = deposit_outflow

    @property
    def deposit_inflow(self):
        return self.__deposit_inflow

    @deposit_inflow.setter
    def deposit_inflow(self, deposit_inflow):
        self.__deposit_inflow = deposit_inflow

    @property
    def net_deposit_flow(self):
        return self.__net_deposit_flow

    @net_deposit_flow.setter
    def net_deposit_flow(self, net_deposit_flow):
        self.__net_deposit_flow = net_deposit_flow

    @property
    def bank_solvent(self):
        return self.__bank_solvent

    @bank_solvent.setter
    def bank_solvent(self, bank_solvent):
        self.__bank_solvent = bank_solvent

    @property
    def bank_capitalized(self):
        return self.__bank_capitalized

    @bank_capitalized.setter
    def bank_capitalized(self, bank_capitalized):
        self.__bank_capitalized = bank_capitalized

    @property
    def defaulted_loans(self):
        return self.__defaulted_loans

    @defaulted_loans.setter
    def defaulted_loans(self, defaulted_loans):
        self.__defaulted_loans = defaulted_loans

    @property
    def credit_failure(self):
        return self.__credit_failure

    @credit_failure.setter
    def credit_failure(self, credit_failure):
        self.__credit_failure = credit_failure

    @property
    def liquidity_failure(self):
        return self.__liquidity_failure

    @liquidity_failure.setter
    def liquidity_failure(self, liquidity_failure):
        self.__liquidity_failure = liquidity_failure

    @property
    def assets_liabilities(self):
        return self.__assets_liabilities

    @assets_liabilities.setter
    def assets_liabilities(self, assets_liabilities):
        self.__assets_liabilities = assets_liabilities

    @property
    def ib_credits_4log(self):
        return self.__ib_credits_4log

    @ib_credits_4log.setter
    def ib_credits_4log(self, ib_credits_4log):
        self.__ib_credits_4log = ib_credits_4log

    @property
    def ib_debits_4log(self):
        return self.__ib_debits_4log

    @ib_debits_4log.setter
    def ib_debits_4log(self, ib_debits_4log):
        self.__ib_debits_4log = ib_debits_4log

    @property
    def ib_interest_income_4log(self):
        return self.__ib_interest_income_4log

    @ib_interest_income_4log.setter
    def ib_interest_income_4log(self, ib_interest_income_4log):
        self.__ib_interest_income_4log = ib_interest_income_4log

    @property
    def ib_interest_expense_4log(self):
        return self.__ib_interest_expense_4log

    @ib_interest_expense_4log.setter
    def ib_interest_expense_4log(self, ib_interest_expense_4log):
        self.__ib_interest_expense_4log = ib_interest_expense_4log

    @property
    def ib_net_interest_income_4log(self):
        return self.__ib_net_interest_income_4log

    @ib_net_interest_income_4log.setter
    def ib_net_interest_income_4log(self, ib_net_interest_income_4log):
        self.__ib_net_interest_income_4log = ib_net_interest_income_4log

    @property
    def ib_credit_loss_4log(self):
        return self.__ib_credit_loss_4log

    @ib_credit_loss_4log.setter
    def ib_credit_loss_4log(self, ib_credit_loss_4log):
        self.__ib_credit_loss_4log = ib_credit_loss_4log

    def get_all_variables(self):
        res =[
            '', # AgtBankId
            '', # SimId
            '', # StepCnt
            self.unique_id,  # BankId
            self.equity,
            self.bank_deposits,
            self.bank_loans,
            self.bank_reserves,
            self.total_assets,
            self.bank_provisions,
            self.bank_new_provisions,
            self.bank_deposits,
            self.ib_credits_4log,
            self.ib_debits_4log,
            self.net_interest_income,
            self.interest_income,
            self.interest_expense,
            self.ib_interest_income_4log,
            self.ib_interest_expense_4log,
            self.ib_net_interest_income_4log,
            self.ib_credit_loss,
            self.rwassets,
            self.bank_dividend,
            self.bank_cum_dividend,
            self.deposit_outflow,
            self.deposit_inflow,
            self.net_deposit_flow,
            self.defaulted_loans,
            self.bank_solvent if self.bank_solvent is None else int(self.bank_solvent),
            self.bank_capitalized if self.bank_capitalized is None else int(self.bank_capitalized),
            self.credit_failure if self.credit_failure is None else int(self.credit_failure),
            self.liquidity_failure if self.liquidity_failure is None else int(self.liquidity_failure),
            '' # Datetime
        ]
        return res
