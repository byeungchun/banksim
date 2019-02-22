import random

from mesaabba.agent.bank import Bank
from mesaabba.agent.loan import Loan
from mesaabba.agent.saver import Saver


def main_risk_weight_optimization(schedule, car):
    for uncap_bank in [x for x in schedule.agents if
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

        for loan in [x for x in schedule.agents if isinstance(x, Loan) and x.pos == uncap_bank.pos and x.loan_approved and x.loan_solvent]:
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

        if uncap_bank.capital_ratio > car:
            # TO DO: colour Green
            uncap_bank.bank_capitalized = True

        savers_in_bank = [x for x in schedule.agents if isinstance(x, Saver) and
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