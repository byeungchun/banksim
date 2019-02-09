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


class Ibloan(Agent):
    ib_rate = None  # interbank loan rate
    ib_amount = None  # intferbank amount
    ib_last_color = None  # used to create visual effects
    ib_creditor = None
    ib_debtor = None

    def __init__(self, unique_id, model,libor_rate=0.01):
        super().__init__(unique_id, model)
        self.ib_rate = libor_rate
        self.ib_amount = 0


class Loan(Agent):
    pdef = None  # true probability of default
    amount = None  # amount of loan - set to unity
    rweight = None  # true risk-weight of the loan
    rwamount = None  # amount * rweight
    lgdamount = None  # loss given default (1-rcvry-rate) * amount
    loan_recovery = None  # rcvry-rate * amount
    rcvry_rate = None  # recovery rate in case of default
    fire_sale_loss = None  # loss percent if sold or removed from bank book
    rating = None  # loan rating - we can specify the rating and then assign pdef from a table - not used
    region_id = None  # Identity of loan's neighborhood - useful for analyzing cross-country/ regional lending patterns
    loan_approved = None  # is loan loan-approved?
    loan_solvent = None  # is loan solvent?
    loan_dumped = None  # loan dumped during risk-weighted-optimization
    loan_liquidated = None  # loan liquidated owing to bank-bankruptcy
    bank_id = None  # identity of lending bank
    rate_quote = None  # rate quoted by lending bank
    rate_reservation = None  # maximum rate borrower is willing to pay [not used here]
    loan_plus_rate = None  # amount * (1 + rate-quote)
    interest_payment = None  # amount * rate-quote
    loan_last_color = None  # used to create visual effects

    def __init__(self, unique_id, model, amount=1, loan_solvent=True, loan_approved=False, loan_dumped=False,
                 loan_liquidated=False,rcvry_rate=0.06, rfree=0):
        super().__init__(unique_id, model)
        self.amount = amount
        self.loan_solvent = loan_solvent
        self.loan_approved = loan_approved
        self.loan_dumped = loan_dumped
        self.loan_liquidated = loan_liquidated
        self.pdef = (np.random.randint(0, 10) + 1) / 100
        self.rweight = 0.5 + (self.pdef * 5.0)
        self.rcvry_rate = rcvry_rate
        self.rate_quote = (((1+rfree) - (self.rcvry_rate * self.pdef)) / (1-self.pdef) -1) * 1.2
        self.lgdamount = (1-self.rcvry_rate) * self.amount
        self.loan_recovery = self.rcvry_rate * self.amount
        self.loan_plus_rate = (1+self.rate_quote) * self.amount
        self.interest_payment = self.rate_quote * self.amount
        self.rwamount = self.rweight * self.amount
        self.fire_sale_loss = np.random.randint(0, 11) / 100


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
    ib_interest_income = None  # interest income, interbank
    ib_interest_expense = None  # interest expense, interbank
    ib_net_interest_income = None  # net interest, interbank
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
    deposit_outflow = None  # deposit withdrawal shock
    deposit_inflow = None  # deposit inflow from other banks
    net_deposit_flow = None  # net deposit flow
    bank_solvent = None  # bank solvent
    bank_capitalized = None  # bank capitalized
    defaulted_loans = None  # amount of defaulted loans
    credit_failure = None  # credit failure
    liquidity_failure = None  # liquidity failure
    assets_liabilities = None  # control variable

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
        self.leverage_ratio = self.equity / self.total_assets

    def calculate_capital_ratio(self):
        self.capital_ratio = self.equity / self.rwassets

    def calculate_reserve_ratio(self):
        self.reserves_ratio = self.bank_reserves / self.bank_deposits

    def calculate_reserve(self):
        self.bank_reserves = self.bank_reserves + self.net_deposit_flow

    def calculate_bank_deposits(self):
        self.bank_deposits = self.bank_deposits + self.net_deposit_flow

    def initialize_ib_variables(self):
        self.ib_credits = 0
        self.ib_debits = 0
        self.ib_interest_income = 0
        self.ib_interest_expense = 0
        self.ib_net_interest_income = 0
        self.ib_credit_loss = 0

    def step(self):
        print('Bank step')
