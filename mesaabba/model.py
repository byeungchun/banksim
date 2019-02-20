from mesa import Model
from mesa.space import MultiGrid, NetworkGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

import logging
import random
import numpy as np
import networkx as nx
import pandas as pd

from mesaabba.agents import Saver, Ibloan, Loan, Bank

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

def get_num_agents(model):
    return len([a for a in model.schedule.agents])

def get_sum_totasset(model):
    return sum([x.total_assets for x in model.schedule.agents if isinstance(x, Bank)])


class MesaAbba(Model):
    height = None
    width = None

    initial_saver = None
    # initial_ibloan = None
    initial_loan = None
    initial_bank = None

    rfree = None  # risk free rate
    car = None  # Capital ratio
    libor_rate = None
    min_reserves_ratio = None

    lst_bank_ratio = list()
    lst_ibloan = list()

    def initialize_deposit_base(self):
        for bank in [x for x in self.schedule.agents if isinstance(x, Bank)]:
            savers = [x for x in self.schedule.agents if isinstance(x, Saver) and x.pos == bank.pos]
            for saver in savers:
                saver.bank_id = bank.pos
                saver.owns_account = True
            bank.bank_deposits = sum([x.balance for x in savers])
            bank.bank_reserves = bank.bank_deposits + bank.equity

    def initialize_loan_book(self):
        for bank in [x for x in self.schedule.agents if isinstance(x, Bank)]:
            bank.bank_reserves = bank.equity + bank.bank_deposits
            bank.calculate_reserve_ratio()
            bank.max_rwa = bank.equity / (1.1 * self.car)
            interim_reserves = bank.bank_reserves
            interim_deposits = bank.bank_deposits
            interim_reserves_ratio = bank.reserves_ratio
            rwa = 0
            unit_loan = 0
            available_loans = True

            for i, loan in enumerate([x for x in self.schedule.agents if
                         isinstance(x, Loan) and bank.pos == x.pos and not x.loan_approved]):
                # This is original script on netlogo. But it spends a lot of time to calculate
                #
                # while available_loans and rwa < bank.max_rwa and \
                #         interim_reserves_ratio > bank.buffer_reserves_ratio * self.min_reserves_ratio:
                #     loans = [x for x in self.schedule.agents if
                #              isinstance(x, Loan) and bank.pos == x.pos and not x.loan_approved]
                #     if len(loans) > 0:
                #         loan = random.choice(loans)
                if available_loans and rwa < bank.max_rwa and \
                        interim_reserves_ratio > bank.buffer_reserves_ratio * self.min_reserves_ratio:
                    interim_reserves = interim_reserves - loan.amount
                    interim_reserves_ratio = interim_reserves / interim_deposits if interim_deposits != 0 else 0
                    loan.loan_approved = True
                    unit_loan = unit_loan + loan.amount
                    rwa = rwa + loan.rweight * loan.amount
                    # TO DO: Change bank node color to yellow
            bank.bank_loans = unit_loan
            bank.rwassets = rwa
            bank.bank_reserves = bank.bank_deposits + bank.equity - bank.bank_loans
            bank.calculate_reserve_ratio()
            bank.calculate_capital_ratio()
            bank.bank_provisions = sum([x.pdef * x.lgdamount for x in self.schedule.agents if isinstance(x, Loan) and
                                        bank.pos == x.pos and x.loan_approved and x.loan_solvent])
            bank.bank_solvent = True
            bank.calculate_total_assets()
            bank.calculate_leverage_ratio()

    def calculate_credit_loss_loan_book(self, solvent_bank):
        loans_with_bank = [x for x in self.schedule.agents if isinstance(x, Loan) and x.pos == solvent_bank.pos and
                           x.loan_approved and x.loan_solvent]
        for loan in loans_with_bank:
            if loan.pdef > random.random():
                loan.loan_solvent = False
                # TO DO: change color to magenta
            loan.rwamount = loan.rweight * loan.amount
        loans_with_bank_default = [x for x in loans_with_bank if not x.loan_solvent]
        # notice that deposits do not change when loans are defaulting
        solvent_bank.rwassets = solvent_bank.rwassets - sum([x.rwamount for x in loans_with_bank_default])
        # Add provision to equity to obtain the total buffer against credit losses,
        # substract losses, and calculate the equity amount before new provisions
        solvent_bank.equity = solvent_bank.equity - sum([x.lgdamount for x in loans_with_bank_default])
        # Calculate the new required level of provisions and substract of equity
        # equity may be negative but do not set the bank to default yet until
        # net income is calculated
        # Notice that banks with negative equity are not allowed to optimize risk-weights
        # - in principle, reducing the loan book could release provisions and make the bank
        # solvent again
        solvent_bank.bank_new_provisions = sum(
            [x.pdef * x.lgdamount for x in self.schedule.agents if isinstance(x, Loan)
             and x.pos == solvent_bank.pos and x.loan_approved and x.loan_solvent])

        change_in_provisions = solvent_bank.bank_new_provisions - solvent_bank.bank_provisions

        solvent_bank.bank_provisions = solvent_bank.bank_new_provisions
        solvent_bank.equity = solvent_bank.equity - change_in_provisions
        solvent_bank.bank_reserves = solvent_bank.bank_reserves + sum([x.loan_recovery for x in loans_with_bank_default])
        solvent_bank.bank_reserves = solvent_bank.bank_reserves - change_in_provisions
        solvent_bank.bank_loans = solvent_bank.bank_loans - sum([x.amount for x in loans_with_bank_default])
        solvent_bank.defaulted_loans = solvent_bank.defaulted_loans + sum([x.amount for x in loans_with_bank_default])
        solvent_bank.calculate_total_assets()

    def calculate_interest_income_loans(self, solvent_bank):
        loans_with_bank = [x for x in self.schedule.agents if isinstance(x, Loan) and x.pos == solvent_bank.pos and
                           x.loan_approved and x.loan_solvent]
        solvent_bank.interest_income = sum([x.interest_payment for x in loans_with_bank])
        solvent_bank.interest_income = solvent_bank.interest_income + \
                                       (solvent_bank.bank_reserves + solvent_bank.bank_provisions) * self.reserve_rates

    def calculate_interest_expense_deposits(self, solvent_bank):
        savers = [x for x in self.schedule.agents if isinstance(x, Saver) and x.pos == solvent_bank.pos]
        solvent_bank.interest_expense = sum([x.balance for x in savers]) * solvent_bank.rdeposits

    def calculate_net_interest_income(self, solvent_bank):
        solvent_bank.net_interest_income = solvent_bank.interest_income - solvent_bank.interest_expense

    def process_unwind_loans_insolvent_bank(self, solvent_bank):
        logging.info('Insolvent bank: %d', solvent_bank.pos)
        # Remember bank enters with negative equity after posting the required provisions
        # so the money available from provisions is:
        # bank-provisions + equity (the latter is negative)
        loans_with_insolvent_bank = [x for x in self.schedule.agents if isinstance(x, Loan) and
                                     x.pos == solvent_bank.pos and x.loan_approved and x.loan_solvent]
        savers_with_insolvent_bank = [x for x in self.schedule.agents if isinstance(x, Saver) and
                                      x.pos == solvent_bank.pos and x.owns_account]
        for saver in savers_with_insolvent_bank:
            saver.owns_account = False
        # Two possible options when bank is insolvent:
        # 0. loans become insolvent, bank recovers recovery from loans
        # is lgdamount the right amount?
        # perhaps it should be rcvry-amount
        # original lines below
        #  let proceeds-from-liquidated-loans sum [ lgdamount] of
        #    loans-with-insolvent-bank
        if self.bankrupt_liquidation == 0:
            proceed_from_loans = sum([x.loan_recovery for x in loans_with_insolvent_bank])
        # 1. loans are sold in the market, and banks suffer fire-sale losses
        elif self.bankrupt_liquidation == 1:
            proceed_from_loans = sum([(1 - x.fire_sale_loss) * x.amount for x in loans_with_insolvent_bank])

        # Notice in this calculation that bank-provisions + equity < bank-provisions
        # since equity is negative for banks forced to unwind loan portfolio
        recovered_funds = np.ceil(solvent_bank.bank_reserves + proceed_from_loans + solvent_bank.bank_provisions + \
                                  solvent_bank.equity)
        # Note that when bank is illiquid, recovered-funds may be negative
        # in this case, the bank cannot pay any of the savers
        if recovered_funds < 0:
            for saver in savers_with_insolvent_bank:
                saver.saver_solvent = False
                saver.balance = 0
                # TO DO: change color to BROWN
        # WHY it counts numbers of savers instead of balance sum???
        if 0 < recovered_funds < len(savers_with_insolvent_bank):
            for saver in random.sample(savers_with_insolvent_bank, int(np.ceil(len(savers_with_insolvent_bank) - recovered_funds))):
                saver.saver_solvent = False
                saver.balance = 0
                # TO DO: change colour to brown

        for loan in loans_with_insolvent_bank:
            loan.bank_id = 9999
            loan.loan_approved = False
            loan.loan_solvent = False
            loan.loan_liquidated = True
            # TO DO: change colour to turquoise
        # they should add to zero 0
        solvent_bank.bank_loans = sum([x.amount for x in self.schedule.agents if isinstance(x, Loan) and
                                       x.pos == solvent_bank.pos and x.loan_approved and x.loan_solvent])
        solvent_bank.bank_deposits = sum([x.balance for x in self.schedule.agents if isinstance(x, Saver) and
                                          x.pos == solvent_bank.pos and x.owns_account])
        solvent_bank.equity = 0
        solvent_bank.bank_reserves = 0
        solvent_bank.reserves_ratio = 0
        solvent_bank.leverage_ratio = 0
        solvent_bank.rwassets = 0
        solvent_bank.bank_solvent = False
        solvent_bank.bank_capitalized = False
        solvent_bank.total_assets = 0
        solvent_bank.capital_ratio = 0
        # TO DO: change colour to red

    # Evaluate solvency of banks after loans experience default
    def main_evaluate_solvency(self):
        for solvent_bank in [x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent]:
            self.calculate_credit_loss_loan_book(solvent_bank)
            self.calculate_interest_income_loans(solvent_bank)
            self.calculate_interest_expense_deposits(solvent_bank)
            self.calculate_net_interest_income(solvent_bank)

            solvent_bank.equity = solvent_bank.equity + solvent_bank.net_interest_income
            solvent_bank.calculate_capital_ratio()

            solvent_bank.bank_reserves = solvent_bank.bank_reserves + solvent_bank.net_interest_income
            solvent_bank.calculate_reserve_ratio()

            if solvent_bank.equity < 0:
                solvent_bank.bank_solvent = False
                solvent_bank.bank_capitalized = False
                solvent_bank.credit_failure = True
                # Change color to Red
                self.process_unwind_loans_insolvent_bank(solvent_bank)

            else:
                if 0 < solvent_bank.capital_ratio < self.car:
                    solvent_bank.bank_capitalized = False
                    solvent_bank.bank_solvent = True
                    # TO DO: change colour to Cyan

                elif solvent_bank.capital_ratio > self.car:
                    solvent_bank.bank_capitalized = True
                    solvent_bank.bank_solvent = True
                    # TO DO: change colour to Green

                solvent_bank.calculate_capital_ratio()
                solvent_bank.calculate_reserve_ratio()
                solvent_bank.calculate_total_assets()
                solvent_bank.calculate_leverage_ratio()

    def calculate_interbank_credit_loss(self, solvent_bank):
        solvent_bank.ib_credit_loss = sum([x.ib_amount for x in self.schedule.agents if isinstance(x, Ibloan) and
                                           x.ib_creditor == solvent_bank and not x.ib_debtor.bank_solvent])

    def calculate_interbank_interest_income(self, solvent_bank):
        # QUESTION: in netlogo script, it is (1 + x.ib_rate). But it looks wrong because it is interest income
        solvent_bank.ib_interest_income = sum(
            [x.ib_amount * (1 + x.ib_rate) for x in self.schedule.agents if isinstance(x, Ibloan) and
             x.ib_creditor == solvent_bank and x.ib_debtor.bank_solvent])

    def calculate_interbank_interest_expense(self, solvent_bank):
        # QUESTION: in netlogo script, it is (1 + x.ib_rate). But it looks wrong because it is interest income
        solvent_bank.ib_interest_expense = sum(
            [x.ib_amount * (1 + x.ib_rate) for x in self.schedule.agents if isinstance(x, Ibloan) and
             x.ib_debtor == solvent_bank])

    def calculate_interbank_net_interest_income(self, solvent_bank):
        solvent_bank.ib_net_interest_income = solvent_bank.ib_interest_income - solvent_bank.ib_interest_expense

    # evaluate second round effects owing to cross-bank linkages
    # only interbank loans to cover shortages in reserves requirements are included
    def main_second_round_effects(self):
        solvent_banks = [x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent]
        insolvent_banks = [x for x in self.schedule.agents if isinstance(x, Bank) and not x.bank_solvent]
        solvent_banks_afterwards = list()
        while len(set(solvent_banks).intersection(solvent_banks_afterwards)) != len(solvent_banks):
            logging.debug('while looping')
            for solvent_bank in solvent_banks:
                self.calculate_interbank_credit_loss(solvent_bank)
                self.calculate_interbank_interest_income(solvent_bank)
                self.calculate_interbank_interest_expense(solvent_bank)
                self.calculate_interbank_net_interest_income(solvent_bank)

                if solvent_bank.ib_net_interest_income > 0:
                    my_ibloans = [x for x in self.schedule.agents if
                                  isinstance(x, Ibloan) and x.ib_creditor == solvent_bank]
                    principal_only = sum([x.ib_amount for x in my_ibloans])
                    interest_only = sum([x.ib_amount * x.ib_rate for x in my_ibloans])
                    solvent_bank.equity = solvent_bank.equity + interest_only - solvent_bank.ib_credit_loss
                    solvent_bank.bank_reserves = solvent_bank.bank_reserves + principal_only + interest_only - \
                                                 solvent_bank.ib_credit_loss
                else:
                    my_ibloans = [x for x in self.schedule.agents if
                                  isinstance(x, Ibloan) and x.ib_debtor == solvent_bank]
                    principal_only = sum([x.ib_amount for x in my_ibloans])
                    interest_only = sum([x.ib_amount * x.ib_rate for x in my_ibloans])
                    solvent_bank.equity = solvent_bank.equity - interest_only
                    solvent_bank.bank_reserves = solvent_bank.bank_reserves - principal_only - interest_only

                solvent_bank.calculate_total_assets()
                solvent_bank.calculate_leverage_ratio()
                solvent_bank.calculate_capital_ratio()
                solvent_bank.calculate_reserve_ratio()

                if solvent_bank.equity < 0 or solvent_bank.bank_reserves < 0:
                    solvent_bank.bank_solvent = False
                    solvent_bank.bank_capitalized = False
                    # TO DO: change colour to RED
                    self.process_unwind_loans_insolvent_bank(solvent_bank)

                if 0 < solvent_bank.capital_ratio < self.car:
                    solvent_bank.bank_capitalized = False
                    solvent_bank.bank_solvent = True
                    # TO DO: change colour to Cyan
                    solvent_bank.calculate_total_assets()
                    solvent_bank.calculate_leverage_ratio()
                    solvent_bank.calculate_capital_ratio()
                    solvent_bank.calculate_reserve_ratio()

                if solvent_bank.capital_ratio > self.car:
                    solvent_bank.bank_capitalized = True
                    solvent_bank.bank_solvent = True
                    # TO DO: change colour to Green
                    solvent_bank.calculate_total_assets()
                    solvent_bank.calculate_leverage_ratio()
                    solvent_bank.calculate_capital_ratio()
                    solvent_bank.calculate_reserve_ratio()

            solvent_banks_afterwards = [x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent]
            if len(solvent_banks) != len(set(solvent_banks_afterwards).intersection(solvent_banks)):
                solvent_banks = solvent_banks_afterwards
                solvent_banks_afterwards = list()
            logging.debug('while looping -end')

        # Question: Why all banks should initialize inter-bank related variables? Bank might lose their equity without reason
        for bank in [x for x in self.schedule.agents if isinstance(x, Bank)]:
            bank.initialize_ib_variables()

        for ibloan in [x for x in self.schedule.agents if isinstance(x, Ibloan)]:
            self.schedule.remove(ibloan)
            self.G.remove_edge(ibloan.ib_creditor.pos, ibloan.ib_debtor.pos)

    def main_risk_weight_optimization(self):
        for uncap_bank in [x for x in self.schedule.agents if
                           isinstance(x, Bank) and not x.bank_capitalized and x.bank_solvent]:
            interim_equity = uncap_bank.equity
            interim_rwassets = uncap_bank.rwassets
            interim_reserves = uncap_bank.bank_reserves
            interim_deposits = uncap_bank.bank_deposits
            interim_capital_ratio = uncap_bank.capital_ratio
            interim_reserve_ratio = uncap_bank.reserves_ratio
            interim_loans = uncap_bank.bank_loans
            interim_provisions = uncap_bank.bank_provisions
            current_capital_ratio = uncap_bank.capital_ratio
            current_equity = uncap_bank.equity
            current_rwassets = uncap_bank.rwassets
            n_dumped_loans = 0

            for loan in [x for x in self.schedule.agents if isinstance(x, Loan) and x.pos == uncap_bank.pos and x.loan_approved and x.loan_solvent]:
                loan_equity = interim_equity - loan.amount * loan.fire_sale_loss + loan.pdef * loan.lgdamount
                loan_rwassets = interim_rwassets - loan.rwamount
                loan_capital_ratio = loan_equity / loan_rwassets if loan_rwassets != 0 else 0
                loan_reserves = interim_reserves - loan.amount * loan.fire_sale_loss + + loan.pdef * loan.lgdamount
                loan_total_balance = interim_loans - loan.amount
                loan_provisions = interim_provisions - loan.pdef * loan.lgdamount
                loan_deposits = interim_deposits

                if loan_capital_ratio > interim_capital_ratio and loan_equity > 0 and loan_rwassets > 0:
                    interim_equity = loan_equity
                    interim_rwassets = loan_rwassets
                    interim_capital_ratio = loan_capital_ratio
                    interim_reserves = loan_reserves
                    interim_loans = loan_total_balance
                    interim_provisions = loan_provisions
                    interim_deposits = interim_deposits - loan.amount
                    loan.loan_dumped = True
                    loan.loan_approved = False
                    # TO DO: color gray
                    n_dumped_loans = n_dumped_loans + 1
            # calculate new balance sheet after risk weight optimization
            # you can check if they are right with the following commands
            #
            # let dumped-loans loans with [bank-id = ? and loan-dumped? = true]
            # let current-loans loans with [bank-id = ? and loan-solvent? and loan-approved? ]

            # set equity equity - sum [ amount * fire-sale-loss] of dumped-loans
            # set rwassets sum [rwamount] of current-loans
            # set bank-loans sum [ amount ] of current-loans

            uncap_bank.equity = interim_equity
            uncap_bank.rwassets = interim_rwassets
            uncap_bank.capital_ratio = interim_capital_ratio
            uncap_bank.bank_reserves = interim_reserves
            uncap_bank.bank_loans = interim_loans
            uncap_bank.total_assets = uncap_bank.bank_reserves + uncap_bank.bank_loans
            uncap_bank.calculate_leverage_ratio()
            uncap_bank.bank_provisions = interim_provisions
            uncap_bank.calculate_reserve_ratio()

            # the following two lines create problems since it reports cumulative dumped-loans
            # hence, the n-dumped-loans in this optimization loop is overstated
            # we have it replaced

            # let dumped-loans loans with [bank-id = ? and loan-dumped? = true]
            # let n-dumped-loans count dumped-loans

            if uncap_bank.capital_ratio > self.car:
                # TO DO: colour Green
                uncap_bank.bank_capitalized = True

            savers_in_bank = [x for x in self.schedule.agents if isinstance(x, Saver) and
                              x.pos == uncap_bank.pos and x.owns_account]
            if n_dumped_loans < len(savers_in_bank):
                for saver in random.sample(savers_in_bank, n_dumped_loans):
                    saver.owns_account = False
                    # TO DO: colour White
            else:
                for saver in savers_in_bank:
                    saver.owns_account = False
                    # TO DO: colour White
                uncap_bank.equity = uncap_bank.equity - (n_dumped_loans - len(savers_in_bank))
            uncap_bank.bank_deposits = sum([x.balance for x in savers_in_bank if x.owns_account])

    def main_pay_dividends(self):
        for cap_bank in [x for x in self.schedule.agents if isinstance(x, Bank) and x.capital_ratio > self.car]:
            if cap_bank.capital_ratio >= cap_bank.upper_bound_cratio:
                # reduce excess capital
                # first by drawing reserves down to the floor
                # afterwards, by deleveraging
                target_capital = cap_bank.upper_bound_cratio * cap_bank.rwassets
                excess_capital = cap_bank.equity - target_capital
                reserves_floor = self.min_reserves_ratio * cap_bank.bank_deposits * cap_bank.buffer_reserves_ratio
                excess_reserves = cap_bank.bank_reserves - reserves_floor

                if excess_capital < excess_reserves:
                    cap_bank.bank_reserves = cap_bank.bank_reserves - excess_capital
                    cap_bank.bank_dividend = cap_bank.equity - target_capital
                    cap_bank.bank_cum_dividend = cap_bank.bank_cum_dividend + cap_bank.bank_dividend
                    cap_bank.equity = target_capital
                    cap_bank.calculate_capital_ratio()
                    cap_bank.calculate_total_assets()
                    cap_bank.calculate_leverage_ratio()
                else:
                    cap_bank.bank_reserves = reserves_floor

                    # let excess_loans excess_capital _ excess_reserves
                    #interim_equity = cap_bank.equity - excess_reserves
                    interim_equity = cap_bank.equity

                    interim_rwassets = cap_bank.rwassets
                    interim_reserves = cap_bank.bank_reserves
                    interim_deposits = cap_bank.bank_deposits
                    #interim_capital_ratio = interim_equity / interim_rwassets if interim_rwassets != 0 else 0
                    interim_capital_ratio  = cap_bank.capital_ratio
                    cap_bank.calculate_reserve_ratio()

                    # let interim-reserve-ratio reserves-ratio
                    interim_loans = cap_bank.bank_loans

                    for loan in [x for x in self.schedule.agents if isinstance(x, Loan) and
                                 cap_bank.pos == x.pos and x.loan_approved and x.loan_solvent]:
                        loan_discount = 0  # no fire_sale of assets when paying dividends, bank is not distressed
                        loan_equity = interim_equity - loan.amount * loan_discount
                        loan_rwassets = interim_rwassets - loan.rwamount
                        loan_capital_ratio = loan_equity / loan_rwassets if loan_rwassets != 0 else 0
                        loan_total_balance = interim_loans - loan.amount

                        if cap_bank.upper_bound_cratio <= loan_capital_ratio < interim_capital_ratio and loan_equity > 0 and loan_rwassets > 0:
                            interim_equity = loan_equity
                            interim_rwassets = loan_rwassets
                            interim_capital_ratio = loan_capital_ratio
                            interim_loans = loan_total_balance
                            loan.loan_dumped = True
                            loan.loan_approved = False
                            # TO DO: change color 86  ; light blue

                    cap_bank.bank_dividend = cap_bank.equity - interim_equity
                    cap_bank.bank_cum_dividend = cap_bank.bank_cum_dividend + cap_bank.bank_dividend
                    cap_bank.equity = interim_equity
                    cap_bank.rwassets = interim_rwassets
                    cap_bank.capital_ratio = cap_bank.equity / cap_bank.rwassets
                    cap_bank.bank_reserves = cap_bank.bank_reserves - cap_bank.bank_dividend
                    cap_bank.total_assets = cap_bank.bank_reserves + cap_bank.bank_loans
                    cap_bank.calculate_leverage_ratio()

    def main_reset_insolvent_loans(self):
        for loan in [x for x in self.schedule.agents if isinstance(x, Loan) and x.loan_approved and not x.loan_solvent]:
            loan.loan_solvent = True
            loan.loan_approved = False
            # TO DO: set color 107

    def main_build_loan_book_locally(self):
        for solvent_bank in [x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_capitalized]:
            desired_reserves_ratio = self.min_reserves_ratio * solvent_bank.buffer_reserves_ratio
            interim_equity = solvent_bank.equity
            interim_rwa = solvent_bank.rwassets
            interim_reserves = solvent_bank.bank_reserves
            interim_deposits = solvent_bank.bank_deposits
            interim_capital_ratio = solvent_bank.capital_ratio
            interim_reserves_ratio = solvent_bank.reserves_ratio
            interim_loans = solvent_bank.bank_loans
            interim_provisions = solvent_bank.bank_provisions

            for avail_loan in [x for x in self.schedule.agents if isinstance(x, Loan) and x.pos == solvent_bank.pos and
                                                                  not x.loan_approved and x.loan_solvent]:

                interim_capital_ratio = (interim_equity - avail_loan.pdef * avail_loan.lgdamount) / \
                                        (interim_rwa + avail_loan.rwamount) if (interim_rwa + avail_loan.rwamount) != 0 else 0
                interim_reserves_ratio = (interim_reserves - avail_loan.pdef * avail_loan.lgdamount - avail_loan.amount) / \
                                        interim_deposits if interim_deposits != 0 else 0
                if interim_capital_ratio > self.car and interim_reserves_ratio > desired_reserves_ratio:
                    interim_rwa = interim_rwa + avail_loan.rwamount
                    interim_equity = interim_equity - avail_loan.pdef * avail_loan.lgdamount
                    interim_reserves = interim_reserves - avail_loan.amount - avail_loan.pdef * avail_loan.lgdamount
                    interim_loans = interim_loans + avail_loan.amount
                    interim_provisions = interim_provisions + avail_loan.pdef * avail_loan.lgdamount
                    avail_loan.loan_approved = True
                    # TO DO: change color yellow
            solvent_bank.rwassets = interim_rwa
            solvent_bank.bank_reserves = interim_reserves
            solvent_bank.bank_loans = interim_loans
            solvent_bank.equity = interim_equity
            solvent_bank.bank_provisions = interim_provisions
            solvent_bank.total_assets = solvent_bank.bank_reserves + solvent_bank.bank_loans

            # ratio has to be calculated since the last calculation in the available_loans loop
            # reports the first instance of the capital ratio that does not meet the CAR

            solvent_bank.capital_ratio = interim_equity / interim_rwa if interim_rwa != 0 else 0
            solvent_bank.calculate_reserve_ratio()
            solvent_bank.calculate_total_assets()
            solvent_bank.calculate_leverage_ratio()

            # assets=liabilities? (equity + bank-deposits + IB-debits) - (bank-loans + bank-reserves + IB-credits)

    def main_build_loan_book_globally(self):
        solvent_banks = [x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_capitalized]
        weak_banks = [x for x in self.schedule.agents if isinstance(x, Bank) and
                      not x.bank_capitalized and not x.bank_solvent]
        avail_loans = list()
        for weak_bank in weak_banks:
            avail_loans.extend([x for x in self.schedule.agents if isinstance(x, Loan) and x.pos == weak_bank.pos and
                                not x.loan_approved and x.loan_solvent])
        for solvent_bank in solvent_banks:
            # TO DO: To give equal change to all solvent banks, change bank randomly

            interim_equity = solvent_bank.equity
            interim_rwa = solvent_bank.rwassets
            interim_reserves = solvent_bank.bank_reserves
            interim_deposits = solvent_bank.bank_deposits
            interim_capital_ratio = 0
            interim_reserve_ratio = solvent_bank.reserves_ratio
            interim_loans = solvent_bank.bank_loans
            interim_provisions = solvent_bank.bank_provisions
            for avail_loan in avail_loans:
                interim_capital_ratio = (interim_equity - avail_loan.pdef * avail_loan.lgdamount) / \
                                        (interim_rwa + avail_loan.rwamount) if (
                                                                                           interim_rwa + avail_loan.rwamount) != 0 else 0
                interim_reserve_ratio = (
                                                    interim_reserves - avail_loan.pdef * avail_loan.lgdamount - avail_loan.amount) / \
                                        interim_deposits if interim_deposits != 0 else 0
                if interim_capital_ratio > self.car and interim_reserve_ratio > self.min_reserves_ratio:
                    interim_rwa = interim_rwa + avail_loan.rwamount
                    interim_reserves = interim_reserves - avail_loan.amount - avail_loan.pdef * avail_loan.lgdamount
                    interim_loans = interim_loans + avail_loan.amount
                    interim_equity = interim_equity - avail_loan.pdef * avail_loan.lgdamount
                    interim_provisions = interim_provisions + avail_loan.pdef * avail_loan.lgdamount
                    avail_loan.loan_approved = True
                    avail_loan.bank_id = solvent_bank.pos
                    avail_loan.pos = solvent_bank.pos

                    # TO DO: change color yellow
            solvent_bank.rwassets = interim_rwa
            solvent_bank.bank_reserves = interim_reserves
            solvent_bank.bank_loans = interim_loans
            solvent_bank.equity = interim_equity
            solvent_bank.bank_provisions = interim_provisions
            solvent_bank.total_assets = solvent_bank.bank_reserves + solvent_bank.bank_loans

            # ratio has to be calculated since the last calculation in the available_loans loop
            # reports the first instance of the capital ratio that does not meet the CAR

            solvent_bank.capital_ratio = interim_equity / interim_rwa if interim_rwa != 0 else 0
            solvent_bank.calculate_reserve_ratio()
            solvent_bank.calculate_total_assets()
            solvent_bank.calculate_leverage_ratio()

            # assets=liabilities? (equity + bank-deposits + IB-debits) - (bank-loans + bank-reserves + IB-credits)

    def process_deposit_withdrawal(self):
        # savers withdraw funds from solvent banks
        # banks that are insolvent have already liquidated their loan portfolio and
        # returned their deposits to savers
        for solvent_bank in [x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent]:
            savers = [x for x in self.schedule.agents if isinstance(x, Saver) and x.pos == solvent_bank.pos and
                      x.saver_solvent and x.owns_account]
            logging.debug('process_deposit_withdrawal- num savers: %d of bank %d',len(savers),solvent_bank.pos)
            for saver in savers:
                if random.random() < saver.withdraw_prob:
                    saver.bank_id = 9999
                    saver.owns_account = False
                    # TO DO: saver.saver_last_color = color
                    # TO DO: change color Red
                    solvent_bank.deposit_outflow = solvent_bank.deposit_outflow + saver.balance
                #solvent_bank.deposit_outflow = sum([x.balance for x in self.schedule.agents if isinstance(x, Saver) and
                #                                    x.pos == solvent_bank.pos and x.bank_id == 9999])

    def process_deposit_reassignment(self):
        cap_bankpos = [x.pos for x in self.schedule.agents if
                       isinstance(x, Bank) and x.bank_solvent and x.bank_capitalized]
        if len(cap_bankpos) == 0:
            cap_bankpos = [x.pos for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent]

        savers = [x for x in self.schedule.agents if isinstance(x, Saver) and x.bank_id == 9999]
        for saver in savers:
            bankpos = random.choice(cap_bankpos)
            saver.bank_id = bankpos
            saver.pos = bankpos
            saver.owns_account = True
            # TO DO: saver.saver_last_color = color

        for solvent_bank in [x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent]:
            solvent_bank.deposit_inflow = sum(
                [x.balance for x in savers if x.pos == solvent_bank.pos and x.owns_account])
            solvent_bank.net_deposit_flow = solvent_bank.deposit_inflow - solvent_bank.deposit_outflow

    def process_deposit_flow_rebalancing(self):
        for solvent_bank in [x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent]:
            solvent_bank.calculate_bank_deposits()
            solvent_bank.calculate_reserve()
            solvent_bank.calculate_reserve_ratio()
            solvent_bank.calculate_total_assets()
            solvent_bank.deposit_inflow = 0
            solvent_bank.deposit_outflow = 0
            solvent_bank.net_deposit_flow = 0

    def process_access_interbank_market(self, bank):
        liq_banks = [x for x in self.schedule.agents if isinstance(x, Bank) and x.capital_ratio >= self.car and
                     x.reserves_ratio > x.buffer_reserves_ratio * self.min_reserves_ratio]
        # for liq_bank in liq_banks:
            # print('Remove this print after implementing below to do')
            # TO DO: change colour to Green
        needed_reserves = self.min_reserves_ratio * bank.bank_deposits - bank.bank_reserves
        # TO DO: change colour to Yellow
        available_reserves = sum([x.bank_reserves - x.buffer_reserves_ratio * self.min_reserves_ratio * x.bank_deposits
                                  for x in liq_banks])

        ib_request = needed_reserves if needed_reserves < available_reserves else available_reserves
        for liq_bank in liq_banks:
            excess_reserve = liq_bank.bank_reserves - liq_bank.buffer_reserves_ratio * self.min_reserves_ratio * \
                             liq_bank.bank_deposits
            liquidity_contribution = excess_reserve * ib_request / available_reserves if available_reserves != 0 else 0
            liq_bank.bank_reserves = liq_bank.bank_reserves - liquidity_contribution
            liq_bank.ib_credits = liq_bank.ib_credits + liquidity_contribution
            liq_bank.calculate_reserve_ratio()

            ibloan = Ibloan(self.next_id(), self, self.libor_rate)
            ibloan.ib_creditor = liq_bank
            ibloan.ib_amount = liquidity_contribution
            ibloan.ib_debtor = bank
            self.schedule.add(ibloan)
            self.G.add_edge(ibloan.ib_creditor.pos, ibloan.ib_debtor.pos)
            # TO DO: change color Red
            # TO DO: set line to thickness 3

        bank.ib_debits = ib_request
        bank.bank_reserves = bank.bank_reserves + bank.ib_debits
        bank.calculate_reserve_ratio()
        bank.calculate_total_assets()

        # TO DO: set assets=liabilities? (equity + bank-deposits + IB-debits) - (bank-loans + bank-reserves + IB-credits)

    def process_evaluate_liquidity_needs(self):
        for solvent_bank in [x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent]:
            solvent_bank.calculate_reserve_ratio()
        liq_cap_banks = [x for x in self.schedule.agents if isinstance(x, Bank) and x.capital_ratio > self.car and
                         x.reserves_ratio > self.min_reserves_ratio]
        for bankrun_bank in [x for x in self.schedule.agents if isinstance(x, Bank) and x.reserves_ratio < 0]:
            self.process_unwind_loans_insolvent_bank(bankrun_bank)
            # TO DO: change color Brown
            bankrun_bank.liquidity_failure = True

        for noliqcap_bank in [x for x in self.schedule.agents if isinstance(x, Bank) and
                                                                 x.reserves_ratio < self.min_reserves_ratio and x.capital_ratio >= self.car]:
            # TO DO: change color Yellow
            self.process_access_interbank_market(noliqcap_bank)

        # Recalculate the number of banks experiencing shortages of reserves
        # it could be the case that some banks attempting to find resources were not
        # able to find all the resources they needed

        #for noliqcap_bank in [x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent and
        #                                                         0 < x.reserves_ratio < self.min_reserves_ratio and not x.bank_capitalized]:
            #print('Remove this print after implementing below to do')
            # TO DO: change colour to Yellow

    def main_evaluate_liquidity(self):

        # the four procedures will cause some banks to have:
        #
        # excess reserves: bank-reserves > minimum-reserves
        # excess reserve deficit, reserves > 0
        #   borrow from banks with excess reserve surplus (if solvent and capitalized)
        #   reserve optimization if not capitalized
        # excess reserve deficit, reserves < 0
        #   bank facing liquidity run - cannot borrow from other banks
        #   reserve optimization - sell loans to build up reserves
        #
        #
        #
        # the deposit-<> procedures simulate the following shocks:
        #
        #   process-deposit-withdrawal: a number of savers close their accounts
        #   process-deposit-reassignment: and open accounts with other banks
        #     both process-deposit-withdrawal and -reassignment are liquidity-neutral
        #     system-wide
        #   process-deposit-flow-rebalancing: all bank-deposits and bank-reserves are
        #     adjusted to reflect the movement in reserves

        self.process_deposit_withdrawal()
        logging.debug('process_deposit_withdrawal')
        self.process_deposit_reassignment()
        self.process_deposit_flow_rebalancing()
        self.process_evaluate_liquidity_needs()

    def main_write_bank_ratios(self):
        for bank in [x for x in self.schedule.agents if isinstance(x, Bank)]:
            self.lst_bank_ratio.append([
                #bank.pos,
                self.car,                   # 0
                self.min_reserves_ratio,    # 1
                bank.capital_ratio,         # 2
                bank.reserves_ratio,        # 3
                bank.leverage_ratio,        # 4
                bank.upper_bound_cratio,    # 5
                bank.buffer_reserves_ratio, # 6
                bank.bank_dividend,         # 7
                bank.bank_cum_dividend,     # 8
                bank.bank_loans,            # 9
                #bank.interest_income,       # 10
                #bank.interest_expense,      # 11
                bank.bank_reserves,         # 12
                bank.bank_deposits,         # 13
                bank.equity,                # 14
                bank.total_assets,          # 15
                bank.rwassets,              # 16
                bank.credit_failure,        # 17
                bank.liquidity_failure      # 18
                #len([x for x in self.schedule.agents if isinstance(x, Saver) and x.pos == bank.pos])
            ])

    def main_write_interbank_links(self):
        for ibloan in [x for x in self.schedule.agents if isinstance(x, Ibloan)]:
            self.lst_ibloan.append([ibloan.ib_creditor.pos, ibloan.ib_debtor.pos, ibloan.ib_amount])

    def __init__(self, height=20, width=20, initial_saver=10000, initial_loan=20000, initial_bank=10,
                 rfree=0.01, car=0.08, min_reserves_ratio=0.03, initial_equity = 100):
        super().__init__()
        self.height = height
        self.width = width
        self.initial_saver = initial_saver
        self.initial_loan = initial_loan
        self.initial_bank = initial_bank
        self.rfree = rfree
        self.reserve_rates = rfree / 2.0  # set reserve rates one half of risk free rate
        self.libor_rate = rfree
        self.bankrupt_liquidation = 1  # 1: it is fire sale of assets, 0: bank liquidates loans at face value
        self.car = car
        self.min_reserves_ratio = min_reserves_ratio
        self.initial_equity = initial_equity
        self.G = nx.empty_graph(self.initial_bank)
        self.grid = NetworkGrid(self.G)
        self.schedule = RandomActivation(self)
        self.datacollector = DataCollector({
            "BankAsset": get_sum_totasset
        })

        for i in range(self.initial_bank):
            bank = Bank(self.next_id(), self, rfree=self.rfree, car=self.car, equity=self.initial_equity)
            self.grid.place_agent(bank, i)
            self.schedule.add(bank)

        for i in range(self.initial_saver):
            saver = Saver(self.next_id(), self)
            #self.grid.place_agent(saver, i % 10)
            self.grid.place_agent(saver, random.choice(list(self.G.nodes)))
            self.schedule.add(saver)

        for i in range(self.initial_loan):
            loan = Loan(self.next_id(), self, rfree=self.rfree)
            bank_id = random.choice(list(self.G.nodes))
            loan.bank_id = bank_id
            self.grid.place_agent(loan, bank_id) # Evenly distributed
            self.schedule.add(loan)

        self.initialize_deposit_base()
        self.initialize_loan_book()

        self.running = True
        self.datacollector.collect(self)

    def step(self):

        # evaluate solvency of banks after loans experience default
        self.main_evaluate_solvency()
        logging.debug('main_evaluate_solvency')
        # evaluate second round effects owing to cross_bank linkages
        # only interbank loans to cover shortages in reserves requirements are included
        self.main_second_round_effects()
        logging.debug('main_second_round_effects')
        # Undercapitalized banks undertake risk_weight optimization
        self.main_risk_weight_optimization()
        logging.debug('main_risk_weight_optimization')
        # banks that are well capitalized pay dividends
        self.main_pay_dividends()
        logging.debug('main_pay_dividends')
        # Reset insolvent loans, i.e. rebirth lending opportunity
        self.main_reset_insolvent_loans()
        logging.debug('main_reset_insolvent_loans')
        # Build up loan book with loans available in bank neighborhood
        self.main_build_loan_book_locally()
        logging.debug('main_build_loan_book_locally')
        # Build up loan book with loans available in other neighborhoods
        self.main_build_loan_book_globally()
        logging.debug('main_build_loan_book_globally')
        # main_raise_deposits_build_loan_book
        # Evaluate liquidity needs related to reserves requirements
        self.main_evaluate_liquidity()
        logging.debug('main_evaluate_liquidity')
        self.main_write_bank_ratios()
        self.main_write_interbank_links()

        self.schedule.step()
        self.datacollector.collect(self)

    def run_model(self, step_count=20):
        for i in range(step_count):
            if i % 10 == 0 or (i+1) == step_count:
                print(" STEP{0:1d} - # of sovent bank: {1:2d}".format(i, len([x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent])))
            self.step()
            if len([x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent]) == 0:
                logging.info("All banks are bankrupt!")
                break
        df_bank = pd.DataFrame(self.lst_bank_ratio)
        df_ibloan = pd.DataFrame(self.lst_ibloan)
        df_bank.columns = ['car','minReservesRatio','capitalRatio','reservesRatio','leverageRatio','upperReservesRatio',
                           'bufferReservesRatio','bankDividend','bankCumDividend','bankLoans','bankReserves',
                           'bankDeposits','equity','totalAssets','rwassets','creditFailure','liquidityFailure']
        df_ibloan.columns = ['ibCreditor','ibDebtor','ibAmount']
        return df_bank, df_ibloan


