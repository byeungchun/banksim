"""
Loan agent
"""

from mesa import Agent
from numpy.random import uniform


class Loan(Agent):

    def __init__(self, params):
        super().__init__(params.get("unique_id"), params.get("model"))
        # amount of loan - set to unity
        self.amount = params.get("amount")
        # is loan solvent?
        self.loan_solvent = params.get("loan_solvent")
        # is loan loan-approved?
        self.loan_approved = params.get("loan_approved")
        # loan dumped during risk-weighted-optimization
        self.loan_dumped = params.get("loan_dumped")
        # loan liquidated owing to bank-bankruptcy
        self.loan_liquidated = params.get("loan_liquidated")
        # true probability of default
        self.pdef = uniform(high=params.get("pdf_upper"))
        # true risk-weight of the loan
        self.rweight = 0.5 + (self.pdef * 5.0)
        # recovery rate in case of default
        self.rcvry_rate = params.get("rcvry_rate")
        # rate quoted by lending bank
        self.rate_quote = (((1 + params.get("rfree")) - (self.rcvry_rate * self.pdef)) / (1 - self.pdef) - 1) * 1.2
        # loss given default (1-rcvry-rate) * amount
        self.lgdamount = (1 - self.rcvry_rate) * self.amount
        # rcvry-rate * amount
        self.loan_recovery = self.rcvry_rate * self.amount
        # amount * (1 + rate-quote)
        self.loan_plus_rate = (1 + self.rate_quote) * self.amount
        # amount * rate-quote
        self.interest_payment = self.rate_quote * self.amount
        # amount * rweight
        self.rwamount = self.rweight * self.amount
        # loss percent if sold or removed from bank book
        self.fire_sale_loss = uniform(high=params.get("firesale_upper"))
        # loan rating - we can specify the rating and then assign pdef from a table - not used
        self.rating = None
        # Identity of loan's neighborhood - useful for analyzing cross-country/ regional lending patterns
        self.region_id = None
        # identity of lending bank
        self.bank_id = None
        # maximum rate borrower is willing to pay [not used here]
        self.rate_reservation = None
        # used to create visual effects
        self.loan_last_color = None

    @property
    def pdef(self):
        return self.__pdef

    @pdef.setter
    def pdef(self, pdef):
        self.__pdef = pdef

    @property
    def amount(self):
        return self.__amount

    @amount.setter
    def amount(self, amount):
        self.__amount = amount

    @property
    def rweight(self):
        return self.__rweight

    @rweight.setter
    def rweight(self, rweight):
        self.__rweight = rweight

    @property
    def lgdamount(self):
        return self.__lgdamount

    @lgdamount.setter
    def lgdamount(self, lgdamount):
        self.__lgdamount = lgdamount

    @property
    def loan_recovery(self):
        return self.__loan_recovery

    @loan_recovery.setter
    def loan_recovery(self, loan_recovery):
        self.__loan_recovery = loan_recovery

    @property
    def rcvry_rate(self):
        return self.__rcvry_rate

    @rcvry_rate.setter
    def rcvry_rate(self, rcvry_rate):
        self.__rcvry_rate = rcvry_rate

    @property
    def fire_sale_loss(self):
        return self.__fire_sale_loss

    @fire_sale_loss.setter
    def fire_sale_loss(self, fire_sale_loss):
        self.__fire_sale_loss = fire_sale_loss

    @property
    def rating(self):
        return self.__rating

    @rating.setter
    def rating(self, rating):
        self.__rating = rating

    @property
    def region_id(self):
        return self.__region_id

    @region_id.setter
    def region_id(self, region_id):
        self.__region_id = region_id

    @property
    def loan_approved(self):
        return self.__loan_approved

    @loan_approved.setter
    def loan_approved(self, loan_approved):
        self.__loan_approved = loan_approved

    @property
    def loan_solvent(self):
        return self.__loan_solvent

    @loan_solvent.setter
    def loan_solvent(self, loan_solvent):
        self.__loan_solvent = loan_solvent

    @property
    def loan_dumped(self):
        return self.__loan_dumped

    @loan_dumped.setter
    def loan_dumped(self, loan_dumped):
        self.__loan_dumped = loan_dumped

    @property
    def loan_liquidated(self):
        return self.__loan_liquidated

    @loan_liquidated.setter
    def loan_liquidated(self, loan_liquidated):
        self.__loan_liquidated = loan_liquidated

    @property
    def bank_id(self):
        return self.__bank_id

    @bank_id.setter
    def bank_id(self, bank_id):
        self.__bank_id = bank_id

    @property
    def rate_quote(self):
        return self.__rate_quote

    @rate_quote.setter
    def rate_quote(self, rate_quote):
        self.__rate_quote = rate_quote

    @property
    def rate_reservation(self):
        return self.__rate_reservation

    @rate_reservation.setter
    def rate_reservation(self, rate_reservation):
        self.__rate_reservation = rate_reservation

    @property
    def loan_plus_rate(self):
        return self.__loan_plus_rate

    @loan_plus_rate.setter
    def loan_plus_rate(self, loan_plus_rate):
        self.__loan_plus_rate = loan_plus_rate

    @property
    def interest_payment(self):
        return self.__interest_payment

    @interest_payment.setter
    def interest_payment(self, interest_payment):
        self.__interest_payment = interest_payment

    @property
    def loan_last_color(self):
        return self.__loan_last_color

    @loan_last_color.setter
    def loan_last_color(self, loan_last_color):
        self.__loan_last_color = loan_last_color

    def get_all_variables(self):
        res = [
            '',  # AgtSaverId
            '',  # SimId
            '',  # StepCnt
            self.unique_id,
            self.pdef,
            self.amount,
            self.rweight,
            self.rwamount,
            self.lgdamount,
            self.loan_recovery,
            self.rcvry_rate,
            self.fire_sale_loss,
            self.rating,
            self.rate_quote,
            self.rate_reservation,
            self.loan_plus_rate,
            self.interest_payment,
            self.region_id,
            self.loan_approved if self.loan_approved is None else int(self.loan_approved),
            self.loan_solvent if self.loan_solvent is None else int(self.loan_solvent),
            self.loan_dumped if self.loan_dumped is None else int(self.loan_dumped),
            self.loan_liquidated if self.loan_liquidated is None else int(self.loan_liquidated),
            self.bank_id if self.bank_id is None else int(self.bank_id),
            '' # datetime
        ]
        return res
