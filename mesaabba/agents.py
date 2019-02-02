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

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)


class Ibloan(Agent):

    ib_rate = None  # interbank loan rate
    ib_amount = None  # intferbank amount
    ib_last_color = None  # used to create visual effects

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)



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

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)


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

    def __init(self, unique_id, model):
        super().__init__(unique_id, model)
