# coding: utf-8

import itertools
from banksim.model import BankSim


def exec_banksim_model(model_params):
    model = BankSim(**model_params)
    model.run_model(step_count=240)
    return True

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


exec_banksim_model(lst_model_params[0])
