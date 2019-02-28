import logging

from banksim.agent.bank import Bank
from banksim.agent.ibloan import Ibloan
from banksim.bankingsystem.f2_eval_solvency import process_unwind_loans_insolvent_bank

def calculate_interbank_credit_loss(schedule, solvent_bank):
    solvent_bank.ib_credit_loss = sum([x.ib_amount for x in schedule.agents if isinstance(x, Ibloan) and
                                       x.ib_creditor == solvent_bank and not x.ib_debtor.bank_solvent])


def calculate_interbank_interest_income(schedule, solvent_bank):
    # QUESTION: in netlogo script, it is (1 + x.ib_rate). But it looks wrong because it is interest income
    solvent_bank.ib_interest_income = sum(
        [x.ib_amount * (1 + x.ib_rate) for x in schedule.agents if isinstance(x, Ibloan) and
         x.ib_creditor == solvent_bank and x.ib_debtor.bank_solvent])


def calculate_interbank_interest_expense(schedule, solvent_bank):
    # QUESTION: in netlogo script, it is (1 + x.ib_rate). But it looks wrong because it is interest income
    solvent_bank.ib_interest_expense = sum(
        [x.ib_amount * (1 + x.ib_rate) for x in schedule.agents if isinstance(x, Ibloan) and
         x.ib_debtor == solvent_bank])


def calculate_interbank_net_interest_income(solvent_bank):
    solvent_bank.ib_net_interest_income = solvent_bank.ib_interest_income - solvent_bank.ib_interest_expense

# evaluate second round effects owing to cross-bank linkages
# only interbank loans to cover shortages in reserves requirements are included
def main_second_round_effects(schedule, bankrupt_liquidation, car, G):
    solvent_banks = [x for x in schedule.agents if isinstance(x, Bank) and x.bank_solvent]
    insolvent_banks = [x for x in schedule.agents if isinstance(x, Bank) and not x.bank_solvent]
    solvent_banks_afterwards = list()
    while len(set(solvent_banks).intersection(solvent_banks_afterwards)) != len(solvent_banks):
        logging.debug('while looping')
        for solvent_bank in solvent_banks:
            calculate_interbank_credit_loss(schedule, solvent_bank)
            calculate_interbank_interest_income(schedule, solvent_bank)
            calculate_interbank_interest_expense(schedule, solvent_bank)
            calculate_interbank_net_interest_income(solvent_bank)

            if solvent_bank.ib_net_interest_income > 0:
                my_ibloans = [x for x in schedule.agents if
                              isinstance(x, Ibloan) and x.ib_creditor == solvent_bank]
                principal_only = sum([x.ib_amount for x in my_ibloans])
                interest_only = sum([x.ib_amount * x.ib_rate for x in my_ibloans])
                solvent_bank.equity = solvent_bank.equity + interest_only - solvent_bank.ib_credit_loss
                solvent_bank.bank_reserves = solvent_bank.bank_reserves + principal_only + interest_only - \
                                             solvent_bank.ib_credit_loss
            else:
                my_ibloans = [x for x in schedule.agents if
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
                process_unwind_loans_insolvent_bank(schedule, bankrupt_liquidation, solvent_bank)

            if 0 < solvent_bank.capital_ratio < car:
                solvent_bank.bank_capitalized = False
                solvent_bank.bank_solvent = True
                # TO DO: change colour to Cyan
                solvent_bank.calculate_total_assets()
                solvent_bank.calculate_leverage_ratio()
                solvent_bank.calculate_capital_ratio()
                solvent_bank.calculate_reserve_ratio()

            if solvent_bank.capital_ratio > car:
                solvent_bank.bank_capitalized = True
                solvent_bank.bank_solvent = True
                # TO DO: change colour to Green
                solvent_bank.calculate_total_assets()
                solvent_bank.calculate_leverage_ratio()
                solvent_bank.calculate_capital_ratio()
                solvent_bank.calculate_reserve_ratio()

        solvent_banks_afterwards = [x for x in schedule.agents if isinstance(x, Bank) and x.bank_solvent]
        if len(solvent_banks) != len(set(solvent_banks_afterwards).intersection(solvent_banks)):
            solvent_banks = solvent_banks_afterwards
            solvent_banks_afterwards = list()
        logging.debug('while looping -end')

    # To clear all ibloan activities
    # Question: Why all banks should initialize inter-bank related variables? Bank might lose their equity without reason
    for bank in [x for x in schedule.agents if isinstance(x, Bank)]:
        bank.initialize_ib_variables()
    for ibloan in [x for x in schedule.agents if isinstance(x, Ibloan)]:
        schedule.remove(ibloan)
        G.remove_edge(ibloan.ib_creditor.pos, ibloan.ib_debtor.pos)
