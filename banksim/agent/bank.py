from mesa import Agent


class Bank(Agent):
    # Balance_sheet components
    #
    equity = None  # equity (capital) of the bank
    bank_deposits = None  # deposits raised by bank
    bank_loans = None  # amount total loans made by bank
    bank_reserves = None  # liquid bank_reserves
    total_assets = None  # bank_loans + bank_reserves
    # Bank buffers
    bank_provisions = None  # provisions against expected losses
    bank_new_provisions = None  # required provisions, not met if bank defaults
    # Prices
    rdeposits = None  # deposit rate
    # interbank loan holdings
    #
    ib_credits = None  # interbank loans to other banks
    ib_debits = None  # interbank loans from other banks
    # Income components
    #
    net_interest_income = None  # net interest income, balance sheet
    interest_income = None  # interest income, loans
    interest_expense = None  # interest expense, depositors
    ib_interest_income = 0  # interest income, interbank
    ib_interest_expense = 0  # interest expense, interbank
    ib_net_interest_income = 0  # net interest, interbank
    ib_credit_loss = None  # credit losses, interbank exposures
    # reporting requirements
    #
    capital_ratio = None  # capital to risk_weighted assets
    reserves_ratio = None  # reserves to deposits
    rwassets = None  # risk_weighted assets
    leverage_ratio = None  # leverage ratio = equity / total_assets
    bank_dividend = None  # dividends
    bank_cum_dividend = None  # cumulative dividends
    # Bank ratios
    #
    upper_bound_cratio = None  # upper_bound of capital ratio
    # if capital ratio exceeds
    # upper_bound excess cpital
    # pay as dividend
    buffer_reserves_ratio = None  # desired buffer or markup over
    # minimum_reserves_ratio
    # random changes to deposit levels
    deposit_outflow = 0  # deposit withdrawal shock
    deposit_inflow = 0  # deposit inflow from other banks
    net_deposit_flow = None  # net deposit flow
    bank_solvent = None  # bank solvent
    bank_capitalized = None  # bank capitalized
    defaulted_loans = None  # amount of defaulted loans
    credit_failure = None  # credit failure
    liquidity_failure = None  # liquidity failure
    assets_liabilities = None  # control variable
    # For Database logging
    ib_credits_4log = None
    ib_debits_4log = None
    ib_interest_income_4log = None
    ib_interest_expense_4log = None
    ib_net_interest_income_4log = None
    ib_credit_loss_4log = None

    def __init__(self, unique_id, model, equity=100, bank_deposits=0, bank_loans=0, bank_reserves=0, rfree=0,
               bank_solvent=True, defaulted_loans=0, bank_capitalized=True, bank_dividend=0, bank_cum_dividend=0,
               car=0.08, buffer_reserves_ratio=1.5, credit_failure=False, liquidity_failure=False, ib_credits=0,
               ib_debits=0):
        super().__init__(unique_id, model)
        self.equity = equity
        self.bank_deposits = bank_deposits
        self.bank_loans = bank_loans
        self.bank_reserves = bank_reserves
        self.rdeposits = rfree  # assumes deposits are risk free
        self.bank_solvent = bank_solvent  # all banks initially solvent
        self.defaulted_loans = defaulted_loans  # defaulted loans
        self.bank_capitalized = bank_capitalized  # all banks initially capitalized
        self.bank_dividend = bank_dividend
        self.bank_cum_dividend = bank_cum_dividend
        self.upper_bound_cratio = 1.5 * car  # set upper bound for capital ratio. set it to large number
        self.buffer_reserves_ratio = buffer_reserves_ratio
        self.credit_failure = credit_failure
        self.liquidity_failure = liquidity_failure
        self.ib_credits = ib_credits
        self.ib_debits = ib_debits

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

    # def step(self):
    #     print('Bank step')
