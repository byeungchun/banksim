import numpy as np
from mesa import Agent


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
                 loan_liquidated=False,rcvry_rate=0.4, rfree=0):
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