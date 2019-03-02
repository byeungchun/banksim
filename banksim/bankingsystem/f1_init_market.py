from banksim.agent.bank import Bank
from banksim.agent.loan import Loan
from banksim.agent.saver import Saver


def initialize_deposit_base(schedule):
    for bank in [x for x in schedule.agents if isinstance(x, Bank)]:
        savers = [x for x in schedule.agents if isinstance(x, Saver) and x.pos == bank.pos]
        for saver in savers:
            saver.bank_id = bank.pos
            saver.owns_account = True
        bank.bank_deposits = sum([x.balance for x in savers])
        bank.bank_reserves = bank.bank_deposits + bank.equity


def initialize_loan_book(schedule, car, min_reserves_ratio):
    for bank in [x for x in schedule.agents if isinstance(x, Bank)]:
        bank.bank_reserves = bank.equity + bank.bank_deposits
        bank.calculate_reserve_ratio()
        bank.max_rwa = bank.equity / (1.1 * car)
        interim_reserves = bank.bank_reserves
        interim_deposits = bank.bank_deposits
        interim_reserves_ratio = bank.reserves_ratio
        rwa = 0
        unit_loan = 0
        available_loans = True

        for i, loan in enumerate([x for x in schedule.agents if
                     isinstance(x, Loan) and bank.pos == x.pos and not x.loan_approved]):
            # This is original script on netlogo. But it spends a lot of time to calculate
            #
            # while available_loans and rwa < bank.max_rwa and \
            #
            #         interim_reserves_ratio > bank.buffer_reserves_ratio * self.min_reserves_ratio:
            #     loans = [x for x in self.schedule.agents if
            #              isinstance(x, Loan) and bank.pos == x.pos and not x.loan_approved]
            #     if len(loans) > 0:
            #         loan = random.choice(loans)
            if available_loans and rwa < bank.max_rwa and \
                    interim_reserves_ratio > bank.buffer_reserves_ratio * min_reserves_ratio:
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
        bank.bank_provisions = sum([x.pdef * x.lgdamount for x in schedule.agents if isinstance(x, Loan) and
                                    bank.pos == x.pos and x.loan_approved and x.loan_solvent])
        bank.bank_solvent = True
        bank.calculate_total_assets()
        bank.calculate_leverage_ratio()