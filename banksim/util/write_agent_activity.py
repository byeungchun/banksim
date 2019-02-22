import pandas as pd

from banksim.agent.bank import Bank
from banksim.agent.ibloan import Ibloan


def main_write_bank_ratios(schedule, lst_bank_ratio, car, min_reserves_ratio):
    for bank in [x for x in schedule.agents if isinstance(x, Bank)]:
        lst_bank_ratio.append([
            #bank.pos,
            car,                   # 0
            min_reserves_ratio,    # 1
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


def main_write_interbank_links(schedule, lst_ibloan):
    for ibloan in [x for x in schedule.agents if isinstance(x, Ibloan)]:
        lst_ibloan.append([ibloan.ib_creditor.pos, ibloan.ib_debtor.pos, ibloan.ib_amount])


def convert_result2dataframe(lst_bank_ratio, lst_ibloan):
    df_bank = pd.DataFrame(lst_bank_ratio)
    df_ibloan = pd.DataFrame(lst_ibloan)
    df_bank.columns = ['car', 'minReservesRatio', 'capitalRatio', 'reservesRatio', 'leverageRatio',
                       'upperReservesRatio',
                       'bufferReservesRatio', 'bankDividend', 'bankCumDividend', 'bankLoans', 'bankReserves',
                       'bankDeposits', 'equity', 'totalAssets', 'rwassets', 'creditFailure', 'liquidityFailure']
    df_ibloan.columns = ['ibCreditor', 'ibDebtor', 'ibAmount']
    return df_bank, df_ibloan