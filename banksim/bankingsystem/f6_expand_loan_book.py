from banksim.agent.bank import Bank
from banksim.agent.loan import Loan


def main_reset_insolvent_loans(schedule):
    for loan in [x for x in schedule.agents if isinstance(x, Loan) and x.loan_approved and not x.loan_solvent]:
        loan.loan_solvent = True
        loan.loan_approved = False
        # TO DO: set color 107


def main_build_loan_book_locally(schedule, min_reserves_ratio, car):
    for solvent_bank in [x for x in schedule.agents if isinstance(x, Bank) and x.bank_capitalized]:
        desired_reserves_ratio = min_reserves_ratio * solvent_bank.buffer_reserves_ratio
        interim_equity = solvent_bank.equity
        interim_rwa = solvent_bank.rwassets
        interim_reserves = solvent_bank.bank_reserves
        interim_deposits = solvent_bank.bank_deposits
        interim_capital_ratio = solvent_bank.capital_ratio
        interim_reserves_ratio = solvent_bank.reserves_ratio
        interim_loans = solvent_bank.bank_loans
        interim_provisions = solvent_bank.bank_provisions

        for avail_loan in [x for x in schedule.agents if isinstance(x, Loan) and x.pos == solvent_bank.pos and
                                                         not x.loan_approved and x.loan_solvent]:

            interim_capital_ratio = (interim_equity - avail_loan.pdef * avail_loan.lgdamount) / \
                                    (interim_rwa + avail_loan.rwamount) if (interim_rwa + avail_loan.rwamount) != 0 else 0
            interim_reserves_ratio = (interim_reserves - avail_loan.pdef * avail_loan.lgdamount - avail_loan.amount) / \
                                    interim_deposits if interim_deposits != 0 else 0
            if interim_capital_ratio > car and interim_reserves_ratio > desired_reserves_ratio:
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


def main_build_loan_book_globally(schedule, car, min_reserves_ratio):
    solvent_banks = [x for x in schedule.agents if isinstance(x, Bank) and x.bank_capitalized]
    weak_banks = [x for x in schedule.agents if isinstance(x, Bank) and
                  not x.bank_capitalized and not x.bank_solvent]
    avail_loans = list()
    for weak_bank in weak_banks:
        avail_loans.extend([x for x in schedule.agents if isinstance(x, Loan) and x.pos == weak_bank.pos and
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
            if interim_capital_ratio > car and interim_reserve_ratio > min_reserves_ratio:
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