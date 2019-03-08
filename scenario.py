# coding: utf-8

from banksim.model import BankSim
from banksim.agent.bank import Bank

# To replicate ABBA model
model_params = {"write_db": True,
                "max_steps": 240,
                "initial_saver": 10000,
                "initial_bank": 10,
                "initial_loan": 20000,
                "initial_equity": 100,
                "car": 0.08,
                "rfree": 0.01,
                "min_reserves_ratio": 0.03
                }

model = BankSim(**model_params)

# Bank status
for x in [x for x in model.schedule.agents if isinstance(x, Bank)]:
    print("Bank{0:1d} - Reserve: {1:5.0f}, Equity: {2:5.0f}, Deposit: {3:5.0f}, Reserve_ratio: {4:5.3f}".
          format(x.pos, x.bank_reserves, x.equity, x.bank_deposits, x.reserves_ratio))

model.run_model(step_count=240)
