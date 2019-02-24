from mesa import Model
from mesa.space import NetworkGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

import logging
import random
import networkx as nx

from banksim.agent.saver import Saver
from banksim.agent.bank import Bank
from banksim.agent.loan import Loan
from banksim.bankingsystem.f1_init_market import initialize_deposit_base
from banksim.bankingsystem.f1_init_market import initialize_loan_book
from banksim.bankingsystem.f2_eval_solvency import main_evaluate_solvency
from banksim.bankingsystem.f3_second_round_effect import main_second_round_effects
from banksim.bankingsystem.f4_optimize_risk_weight import main_risk_weight_optimization
from banksim.bankingsystem.f5_pay_dividends import main_pay_dividends
from banksim.bankingsystem.f6_expand_loan_book import main_reset_insolvent_loans
from banksim.bankingsystem.f6_expand_loan_book import main_build_loan_book_locally
from banksim.bankingsystem.f6_expand_loan_book import main_build_loan_book_globally
from banksim.bankingsystem.f7_eval_liquidity import main_evaluate_liquidity
from banksim.util.write_agent_activity import main_write_bank_ratios
from banksim.util.write_agent_activity import convert_result2dataframe
from banksim.util.write_agent_activity import main_write_interbank_links

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


def get_sum_totasset(model):
    return sum([x.total_assets for x in model.schedule.agents if isinstance(x, Bank)])


class BankSim(Model):
    height = None
    width = None
    initial_saver = None
    initial_loan = None
    initial_bank = None
    rfree = None  # risk free rate
    car = None  # Capital Requirement
    libor_rate = None
    min_reserves_ratio = None

    lst_bank_ratio = list()
    lst_ibloan = list()

    def __init__(self, height=20, width=20, initial_saver=10000, initial_loan=20000, initial_bank=10,
                 rfree=0.01, car=0.08, min_reserves_ratio=0.03, initial_equity = 100):
        super().__init__()
        self.height = height
        self.width = width
        self.initial_saver = initial_saver
        self.initial_loan = initial_loan
        self.initial_bank = initial_bank
        self.rfree = rfree
        self.reserve_rates = rfree / 2.0  # set reserve rates one half of risk free rate
        self.libor_rate = rfree
        self.bankrupt_liquidation = 1  # 1: it is fire sale of assets, 0: bank liquidates loans at face value
        self.car = car
        self.min_reserves_ratio = min_reserves_ratio
        self.initial_equity = initial_equity
        self.G = nx.empty_graph(self.initial_bank)
        self.grid = NetworkGrid(self.G)
        self.schedule = RandomActivation(self)
        self.datacollector = DataCollector({
            "BankAsset": get_sum_totasset
        })

        for i in range(self.initial_bank):
            bank = Bank(self.next_id(), self, rfree=self.rfree, car=self.car, equity=self.initial_equity)
            self.grid.place_agent(bank, i)
            self.schedule.add(bank)

        for i in range(self.initial_saver):
            saver = Saver(self.next_id(), self)
            self.grid.place_agent(saver, random.choice(list(self.G.nodes)))
            self.schedule.add(saver)

        for i in range(self.initial_loan):
            loan = Loan(self.next_id(), self, rfree=self.rfree)
            bank_id = random.choice(list(self.G.nodes))
            loan.bank_id = bank_id
            self.grid.place_agent(loan, bank_id) # Evenly distributed
            self.schedule.add(loan)

        initialize_deposit_base(self.schedule)
        initialize_loan_book(self.schedule, self.car, self.min_reserves_ratio)

        self.running = True
        self.datacollector.collect(self)

    def step(self):

        # evaluate solvency of banks after loans experience default
        main_evaluate_solvency(self.schedule, self.reserve_rates, self.bankrupt_liquidation, self.car)

        # evaluate second round effects owing to cross_bank linkages
        # only interbank loans to cover shortages in reserves requirements are included
        main_second_round_effects(self.schedule, self.bankrupt_liquidation, self.car, self.G)

        # Undercapitalized banks undertake risk_weight optimization
        main_risk_weight_optimization(self.schedule, self.car)

        # banks that are well capitalized pay dividends
        main_pay_dividends(self.schedule, self.car, self.min_reserves_ratio)

        # Reset insolvent loans, i.e. rebirth lending opportunity
        main_reset_insolvent_loans(self.schedule)

        # Build up loan book with loans available in bank neighborhood
        main_build_loan_book_locally(self.schedule, self.min_reserves_ratio, self.car)

        # Build up loan book with loans available in other neighborhoods
        main_build_loan_book_globally(self.schedule, self.car, self.min_reserves_ratio)

        # main_raise_deposits_build_loan_book
        # Evaluate liquidity needs related to reserves requirements
        main_evaluate_liquidity(self.schedule, self.car, self.min_reserves_ratio, self.bankrupt_liquidation)

        main_write_bank_ratios(self.schedule, self.lst_bank_ratio, self.car, self.min_reserves_ratio)
        main_write_interbank_links(self.schedule, self.lst_ibloan)

        self.schedule.step()
        self.datacollector.collect(self)

    def run_model(self, step_count=20):
        for i in range(step_count):
            if i % 10 == 0 or (i+1) == step_count:
                print(" STEP{0:1d} - # of sovent bank: {1:2d}".format(i, len([x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent])))
            self.step()
            if len([x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent]) == 0:
                logging.info("All banks are bankrupt!")
                break
        df_bank, df_ibloan = convert_result2dataframe(self.lst_bank_ratio, self.lst_ibloan)
        return df_bank, df_ibloan
