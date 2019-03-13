# coding: utf-8

import itertools
import concurrent.futures

from banksim.logger import get_logger
from banksim.model import BankSim
from banksim.util.write_sqlitedb import init_database
from banksim.agent.bank import Bank

# To replicate the simulation result in this paper (ABBA: An Agent-Based Model of the Banking System - IMF)
#
#

logger = get_logger("scenario")


def exec_banksim_model(model_params):
    model = BankSim(**model_params)
    model.run_model(step_count=240)
    return True


def main(rep_count=1):

    init_database()

    for i in range(rep_count):
        model_params = {"init_db": False,
                        "write_db": True,
                        "max_steps": 240,
                        "initial_saver": 10000,
                        "initial_bank": 10,
                        "initial_loan": 20000,
                        "initial_equity": 100,
                        "rfree": 0.01
                        }

        lst_capital_req = [0.04, 0.08, 0.12, 0.16]
        lst_reserve_ratio = [0.03, 0.045, 0.06]
        combination_car_res = list(itertools.product(lst_capital_req, lst_reserve_ratio))

        lst_model_params = list()
        for x in combination_car_res:
            model_params["car"] = x[0]
            model_params["min_reserves_ratio"] = x[1]
            lst_model_params.append(model_params.copy())

        with concurrent.futures.ProcessPoolExecutor() as executor:
            model_finish_cnt = 0
            for res in executor.map(exec_banksim_model, lst_model_params):
                if res:
                    model_finish_cnt = model_finish_cnt + 1
                    if model_finish_cnt % 10 == 0:
                        logger.info('Number of completed scenario: %3d', model_finish_cnt)

# Bank status
# for x in [x for x in model.schedule.agents if isinstance(x, Bank)]:
#     print("Bank{0:1d} - Reserve: {1:5.0f}, Equity: {2:5.0f}, Deposit: {3:5.0f}, Reserve_ratio: {4:5.3f}".
#           format(x.pos, x.bank_reserves, x.equity, x.bank_deposits, x.reserves_ratio))


if __name__ == "__main__":
    main(rep_count=100)
