"""
Test for loan initialization

"""
import sys
import unittest
import numpy as np

from banksim.model import BankSim
from banksim.agent.loan import Loan


class TestLoan(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.model_params = {"init_db": False,
                        "write_db": False,
                        "max_steps": 10,
                        "initial_saver": 10000,
                        "initial_bank": 10,
                        "initial_loan": 20000,
                        "initial_equity": 100,
                        "rfree": 0.01,
                        "car": 0.08,
                        "min_reserves_ratio": 0.03
                        }
        cls.model = BankSim(**cls.model_params)

    def test_loan(self):
        self.model.step()
        loans = [x.bank_id for x in self.model.schedule.agents if isinstance(x, Loan)]
        number_per_bank = [loans.count(x) for x in set(loans)]
        print(number_per_bank)
        # Numbers of loans per Banks should be similar
        self.assertEquals(np.sum(number_per_bank), self.model_params["initial_loan"])


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLoan)
    unittest.TextTestRunner(verbosity=2, stream=sys.stderr).run(suite)
