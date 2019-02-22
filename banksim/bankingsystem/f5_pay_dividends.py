from banksim.agent.bank import Bank
from banksim.agent.loan import Loan


def main_pay_dividends(schedule, car, min_reserves_ratio):
    for cap_bank in [x for x in schedule.agents if isinstance(x, Bank) and x.capital_ratio > car]:
        if cap_bank.capital_ratio >= cap_bank.upper_bound_cratio:
            # reduce excess capital
            # first by drawing reserves down to the floor
            # afterwards, by deleveraging
            target_capital = cap_bank.upper_bound_cratio * cap_bank.rwassets
            excess_capital = cap_bank.equity - target_capital
            reserves_floor = min_reserves_ratio * cap_bank.bank_deposits * cap_bank.buffer_reserves_ratio
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

                for loan in [x for x in schedule.agents if isinstance(x, Loan) and
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