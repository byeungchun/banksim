import logging
import random

import numpy as np

from banksim.agent.bank import Bank
from banksim.agent.loan import Loan
from banksim.agent.saver import Saver


def calculate_credit_loss_loan_book(schedule, solvent_bank):
    loans_with_bank = [x for x in schedule.agents if isinstance(x, Loan) and x.pos == solvent_bank.pos and
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
        [x.pdef * x.lgdamount for x in schedule.agents if isinstance(x, Loan)
         and x.pos == solvent_bank.pos and x.loan_approved and x.loan_solvent])

    change_in_provisions = solvent_bank.bank_new_provisions - solvent_bank.bank_provisions

    solvent_bank.bank_provisions = solvent_bank.bank_new_provisions
    solvent_bank.equity = solvent_bank.equity - change_in_provisions
    solvent_bank.bank_reserves = solvent_bank.bank_reserves + sum([x.loan_recovery for x in loans_with_bank_default])
    solvent_bank.bank_reserves = solvent_bank.bank_reserves - change_in_provisions
    solvent_bank.bank_loans = solvent_bank.bank_loans - sum([x.amount for x in loans_with_bank_default])
    solvent_bank.defaulted_loans = solvent_bank.defaulted_loans + sum([x.amount for x in loans_with_bank_default])
    solvent_bank.calculate_total_assets()


def calculate_interest_income_loans(schedule, reserve_rates, solvent_bank):
    loans_with_bank = [x for x in schedule.agents if isinstance(x, Loan) and x.pos == solvent_bank.pos and
                       x.loan_approved and x.loan_solvent]
    solvent_bank.interest_income = sum([x.interest_payment for x in loans_with_bank])
    solvent_bank.interest_income = solvent_bank.interest_income + \
                                   (solvent_bank.bank_reserves + solvent_bank.bank_provisions) * reserve_rates


def calculate_interest_expense_deposits(schedule, solvent_bank):
    savers = [x for x in schedule.agents if isinstance(x, Saver) and x.pos == solvent_bank.pos]
    solvent_bank.interest_expense = sum([x.balance for x in savers]) * solvent_bank.rdeposits


def calculate_net_interest_income(solvent_bank):
    solvent_bank.net_interest_income = solvent_bank.interest_income - solvent_bank.interest_expense


def process_unwind_loans_insolvent_bank(schedule, bankrupt_liquidation, solvent_bank):
    logging.info('Insolvent bank: %d', solvent_bank.pos)
    # Remember bank enters with negative equity after posting the required provisions
    # so the money available from provisions is:
    # bank-provisions + equity (the latter is negative)
    loans_with_insolvent_bank = [x for x in schedule.agents if isinstance(x, Loan) and
                                 x.pos == solvent_bank.pos and x.loan_approved and x.loan_solvent]
    savers_with_insolvent_bank = [x for x in schedule.agents if isinstance(x, Saver) and
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
    if bankrupt_liquidation == 0:
        proceed_from_loans = sum([x.loan_recovery for x in loans_with_insolvent_bank])
    # 1. loans are sold in the bankingsystem, and banks suffer fire-sale losses
    elif bankrupt_liquidation == 1:
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
    solvent_bank.bank_loans = sum([x.amount for x in schedule.agents if isinstance(x, Loan) and
                                   x.pos == solvent_bank.pos and x.loan_approved and x.loan_solvent])
    solvent_bank.bank_deposits = sum([x.balance for x in schedule.agents if isinstance(x, Saver) and
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


def main_evaluate_solvency(schedule, reserve_rates, bankrupt_liquidation, car):
    for solvent_bank in [x for x in schedule.agents if isinstance(x, Bank) and x.bank_solvent]:
        calculate_credit_loss_loan_book(schedule, solvent_bank)
        calculate_interest_income_loans(schedule, reserve_rates, solvent_bank)
        calculate_interest_expense_deposits(schedule, solvent_bank)
        calculate_net_interest_income(solvent_bank)

        solvent_bank.equity = solvent_bank.equity + solvent_bank.net_interest_income
        solvent_bank.calculate_capital_ratio()

        solvent_bank.bank_reserves = solvent_bank.bank_reserves + solvent_bank.net_interest_income
        solvent_bank.calculate_reserve_ratio()

        if solvent_bank.equity < 0:
            solvent_bank.bank_solvent = False
            solvent_bank.bank_capitalized = False
            solvent_bank.credit_failure = True
            # Change color to Red
            process_unwind_loans_insolvent_bank(schedule, bankrupt_liquidation, solvent_bank)

        else:
            if 0 < solvent_bank.capital_ratio < car:
                solvent_bank.bank_capitalized = False
                solvent_bank.bank_solvent = True
                # TO DO: change colour to Cyan

            elif solvent_bank.capital_ratio > car:
                solvent_bank.bank_capitalized = True
                solvent_bank.bank_solvent = True
                # TO DO: change colour to Green

            solvent_bank.calculate_capital_ratio()
            solvent_bank.calculate_reserve_ratio()
            solvent_bank.calculate_total_assets()
            solvent_bank.calculate_leverage_ratio()