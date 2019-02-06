from mesa import Model
from mesa.space import MultiGrid, NetworkGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

import random
import numpy as np
import networkx as nx

from mesaabba.agents import Saver, Ibloan, Loan, Bank


def get_num_agents(model):
    return len([a for a in model.schedule.agents])


class MesaAbba(Model):
    height = None
    width = None

    initial_saver = None
    initial_ibloan = None
    initial_loan = None
    initial_bank = None

    rfree = None  # risk free rate
    car = None  # Capital ratio
    libor_rate = None
    min_reserves_ratio = None

    def initialize_deposit_base(self):
        for i in self.G.nodes:
            bank = [x for x in self.G.nodes[i]['agent'] if isinstance(x, Bank)][0]
            savers = [x for x in self.G.nodes[i]['agent'] if isinstance(x, Saver)]
            bank.bank_deposits = sum([x.balance for x in savers]) + bank.equity
            bank.bank_reserves = bank.bank_deposits * self.min_reserves_ratio

    def initialize_loan_book(self):
        for bank in [x for x in self.schedule.agents if isinstance(x, Bank)]:
            bank.bank_reserves = bank.bank_deposits * self.min_reserves_ratio
            bank.reserves_ratio = bank.bank_reserves / bank.bank_deposits
            bank.max_rwa = bank.equity / (1.1 * self.car)
            interim_reserves = bank.bank_reserves
            interim_deposits = bank.bank_deposits
            interim_reserves_ratio = bank.reserves_ratio
            rwa = 0
            unit_loan = 0
            available_loans = True

            while available_loans and rwa < bank.max_rwa and \
                interim_reserves_ratio > bank.buffer_reserves_ratio * self.min_reserves_ratio:
                loans = [x for x in self.schedule.agents if isinstance(x, Loan) and bank.pos == x.pos and not x.loan_approved]
                if len(loans) > 0:
                    loan = random.choice(loans)
                    interim_reserves = interim_reserves - loan.amount
                    interim_reserves_ratio = interim_reserves / interim_deposits
                    loan.loan_approved = True
                    unit_loan = unit_loan + loan.amount
                    # TO DO: Change bank node color to yellow
            bank.bank_loans = unit_loan
            bank.rwassets = rwa
            bank.bank_reserves = bank.bank_deposits + bank.equity - bank.bank_loans
            bank.reserves_ratio = bank.bank_reserves / bank.bank_deposits
            bank.capital_ratio = bank.equity / bank.rwassets
            bank.bank_provisions = sum([x.pdef * x.lgdamount for x in self.schedule.agents if isinstance(x, Loan) and
                                        bank.pos == x.pos and x.loan_approved and x.loan_solvent])
            bank.bank_solvent = True
            bank.total_assets =  bank.bank_loans + bank.bank_reserves
            bank.leverage_ratio = bank.equity / bank.total_assets

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
        # Add provisiosn to equity to obtain the total buffer against credit losses,
        # substract losses, and calculate the equity amount before new provisions
        solvent_bank.equity = solvent_bank.equity - sum([x.lgdamount for x in loans_with_bank_default])
        # Calculate the new required level of provisions and substract of equity
        # equity may be negative but do not set the bank to default yet until
        # net income is calculated
        # Notice that banks with negative equity are not allowed to optimize risk-weights
        # - in principle, reducing the loan book could release provisions and make the bank
        # solvent again
        solvent_bank.bank_new_provisions = sum([x.pdef * x.lgdamount for x in self.schedule.agents if isinstance(x, Loan)
                                            and x.pos == solvent_bank.pos and x.loan_approved and x.loan_solvent])
        change_in_provisions = solvent_bank.bank_new_provisions - solvent_bank.bank_provisions
        solvent_bank.bank_provisions = solvent_bank.bank_new_provisions
        solvent_bank.equity = solvent_bank.equity - change_in_provisions
        solvent_bank.bank_reserves = solvent_bank.bank_reserves + sum([x.loan_recovery for x in loans_with_bank_default])
        solvent_bank.bank_reserves = solvent_bank.bank_reserves - change_in_provisions
        solvent_bank.bank_loans = solvent_bank.bank_loans - sum([x.amount for x in loans_with_bank_default])
        solvent_bank.defaulted_loans = solvent_bank.defaulted_loans + sum([x.amount for x in loans_with_bank_default])
        solvent_bank.total_assets = solvent_bank.bank_reserves + solvent_bank.bank_loans

    def calculate_interest_income_loans(self, solvent_bank):
        loans_with_bank = [x for x in self.schedule.agents if isinstance(x, Loan) and x.pos == solvent_bank.pos and
                           x.loan_approved and x.loan_solvent]
        solvent_bank.interest_income = sum([x.interest_payment for x in loans_with_bank])
        solvent_bank.interest_income = solvent_bank.interest_income + \
                                       (solvent_bank.bank_reserves + solvent_bank.bank_provisions) * self.reserve_rates

    def calculate_interest_expense_deposits(self, solvent_bank):
        loans_with_bank = [x for x in self.schedule.agents if isinstance(x, Loan) and x.pos == solvent_bank.pos and
                           x.loan_approved and x.loan_solvent]
        solvent_bank.interest_expense = sum([x.balance for x in loans_with_bank])
        solvent_bank.interest_expense = solvent_bank.interest_expense * solvent_bank.rdeposits

    def calculate_net_interest_income(self, solvent_bank):
        solvent_bank.net_interest_income = solvent_bank.interest_income - solvent_bank.interest_expense

    def process_unwind_loans_insolvent_bank(self, solvent_bank):
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
            proceed_from_loans = sum([x.lgdamount for x in loans_with_insolvent_bank])
        # 1. loans are sold in the market, and banks suffer fire-sale losses
        elif self.bankrupt_liquidation == 1:
            proceed_from_loans = sum([(1 - x.fire_sale_loss) * x.amount for x in loans_with_insolvent_bank])

        # Notice in this calculation that bank-provisions + equity < bank-provisions
        # since equity is negative for banks forced to unwind loan portfolio
        recovered_funds = np.ceil(solvent_bank.bank_reserves + proceed_from_loans + solvent_bank.bank_provisions +\
                          solvent_bank.equity)
        # Note that when bank is illiquid, recovered-funds may be negative
        # in this case, the bank cannot pay any of the savers
        if recovered_funds < 0:
            for saver in savers_with_insolvent_bank:
                saver.saver_solvent = False
                saver.balance = 0
                # TO DO: change color to BROWN
        # WHY it counts numbers of savers instead of balance sum???
        if recovered_funds < len(savers_with_insolvent_bank) and recovered_funds > 0:
            for saver in random.sample(savers_with_insolvent_bank, len(savers_with_insolvent_bank) - recovered_funds):
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
        solvent_bank.bank_loans = sum([[x.amount for x in self.schedule.agents if isinstance(x, Loan) and
                                     x.pos == solvent_bank.pos and x.loan_approved and x.loan_solvent]])
        solvent_bank.bank_deposits = sum([x.balance for x in self.schedule.agents if isinstance(x, Saver) and
                                     x.pos == solvent_bank.pos and x.owns_account])
        solvent_bank.equity = 0
        solvent_bank.bank_reserves = 0
        solvent_bank.reserves_ratio = 0
        solvent_bank.leverage_ratio = 0
        solvent_bank.rwassets = 0
        solvent_bank.bank_solvent_bank = False
        solvent_bank.bank_capitalized = False
        solvent_bank.total_assets = 0
        solvent_bank.capital_ratio = 0
        # TO DO: change colour to red


    def main_evaluate_solvency(self):
        for solvent_bank in [x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent]:
            self.calculate_credit_loss_loan_book(solvent_bank)
            self.calculate_interest_income_loans(solvent_bank)
            self.calculate_interest_expense_deposits(solvent_bank)
            self.calculate_net_interest_income(solvent_bank)

            solvent_bank.equity = solvent_bank.equity + solvent_bank.net_interest_income
            solvent_bank.capital_ratio = solvent_bank.equity / solvent_bank.bank_deposits

            if solvent_bank.equity < 0:
                solvent_bank.bank_solvent = False
                solvent_bank.bank_capitalized = False
                solvent_bank.credit_failure = True
                # Change color to Red
                self.process_unwind_loans_insolvent_bank(solvent_bank)



    def __init__(self, height=20, width=20, initial_saver=10000, initial_ibloan=10, initial_loan=50, initial_bank=10,
                 rfree=0.01, car=0.08, min_reserves_ratio = 0.03):
        super().__init__()
        self.height = height
        self.width = width
        self.initial_saver = initial_saver
        self.initial_ibloan = initial_ibloan
        self.initial_loan = initial_loan
        self.initial_bank = initial_bank
        self.rfree = rfree
        self.reserve_rates = rfree / 2.0  # set reserve rates one half of risk free rate
        self.libor_rate = rfree
        self.bankrupt_liquidation = 1  # 1: it is fire sale of assets, 0: bank liquidates loans at face value
        self.car = car
        self.min_reserves_ratio = min_reserves_ratio

        self.G = nx.complete_graph(self.initial_bank)
        self.grid = NetworkGrid(self.G)
        self.schedule = RandomActivation(self)
        self.datacollector = DataCollector({
            "Saver": get_num_agents,
            "Bank": get_num_agents
        })

        for i in range(self.initial_bank):
            bank = Bank(self.next_id(), self, rfree=self.rfree, car=self.car)
            self.grid.place_agent(bank, i)
            self.schedule.add(bank)

        for i in range(self.initial_saver):
            saver = Saver(self.next_id(), self)
            self.grid.place_agent(saver, i % 10)
            self.schedule.add(saver)

        for i in range(self.initial_ibloan):
            ibloan = Ibloan(self.next_id(), self,libor_rate=self.libor_rate)
            self.schedule.add(ibloan)

        for i in range(self.initial_loan):
            loan = Loan(self.next_id(), self, rfree=self.rfree)
            self.grid.place_agent(loan, i % 10)
            self.schedule.add(loan)

        self.running = True
        self.datacollector.collect(self)


    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

    def run_model(self, step_count=200):
        for i in range(step_count):
            self.step()
