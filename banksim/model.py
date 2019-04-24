from mesa import Model
from mesa.space import NetworkGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from datetime import datetime, timezone
import traceback, random
import sqlite3
import networkx as nx
import configparser

from banksim.logger import get_logger
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
from banksim.util.write_sqlitedb import insert_simulation_table, insert_agtbank_table, init_database

logger = get_logger("model")


def get_sum_totasset(model):
    return sum([x.total_assets for x in model.schedule.agents if isinstance(x, Bank)])


class BankSim(Model):
    simid = None #Simulation ID for SQLITEDB primary key
    max_steps = 200
    conn = None # Sqlite connector
    db_cursor = None # Sqlite DB cursor
    lst_bank_ratio = list()
    lst_ibloan = list()

    def __init__(self, **params):
        super().__init__()
        config = configparser.ConfigParser()
        config.read('conf/config.ini')
        self.sqlite_db = config['SQLITEDB']['file']
        self.height = 20
        self.width = 20
        self.is_init_db = False if params.get('write_db') is None else params.get('write_db')
        self.is_write_db = False if params.get('write_db') is None else params.get('write_db')
        self.max_steps = params['max_steps']
        self.initial_saver = params['initial_saver']
        self.initial_loan = params['initial_loan']
        self.initial_bank = params['initial_bank']
        self.rfree = params['rfree']
        self.reserve_rates = params['rfree'] / 2.0  # set reserve rates one half of risk free rate
        self.libor_rate = params['rfree']
        self.bankrupt_liquidation = 1  # 1: it is fire sale of assets, 0: bank liquidates loans at face value
        self.car = params['car']
        self.min_reserves_ratio = params['min_reserves_ratio']
        self.initial_equity = params['initial_equity']
        self.G = nx.empty_graph(self.initial_bank)
        self.grid = NetworkGrid(self.G)
        self.schedule = RandomActivation(self)
        self.datacollector = DataCollector({
            "BankAsset": get_sum_totasset
        })

    def step(self):
        if self.schedule.steps == 0:

            if self.is_init_db:
                init_database()
                logger.info('db initialization')

            if self.is_write_db:
                self.conn = sqlite3.connect(self.sqlite_db)
                self.db_cursor = self.conn.cursor()
                self.simid = int(datetime.now().strftime('%y%m%d%H%M%S%f')[:-3])
                title = 'CAR {0:f}, Reserves Ratio {1:f}'.format(self.car, self.min_reserves_ratio)
                task = (self.simid, title, datetime.now(timezone.utc))
                insert_simulation_table(self.db_cursor, task)

            for i in range(self.initial_bank):
                bank = Bank({'unique_id': self.next_id(), 'model': self, 'equity': 100, 'rfree': self.rfree,
                             'car': self.car, 'buffer_reserves_ratio': 1.5})
                self.grid.place_agent(bank, i)
                self.schedule.add(bank)

            for i in range(self.initial_saver):
                saver = Saver({'unique_id': self.next_id(), 'model': self, 'balance': 1, 'owns_account': False,
                               'saver_solvent': True, 'saver_exit': False, 'withdraw_upperbound': 0.2,
                               'exitprob_upperbound': 0.06})
                self.grid.place_agent(saver, random.choice(list(self.G.nodes)))
                self.schedule.add(saver)

            for i in range(self.initial_loan):
                loan = Loan({"unique_id": self.next_id(), "model": self, "rfree": self.rfree, "amount": 1,
                             "loan_solvent": True, "loan_approved": False, "loan_dumped": False,
                             "loan_liquidated": False,
                             "pdf_upper": 0.1, "rcvry_rate": 0.4, "firesale_upper": 0.1})
                bank_id = random.choice(list(self.G.nodes))
                loan.bank_id = bank_id
                self.grid.place_agent(loan, bank_id)  # Evenly distributed
                self.schedule.add(loan)

            initialize_deposit_base(self.schedule)
            initialize_loan_book(self.schedule, self.car, self.min_reserves_ratio)

            self.running = True
            self.datacollector.collect(self)

        if self.schedule.steps == self.max_steps:
            self.running = False

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

        if self.is_write_db:
            # Insert agent variables of current step into SQLITEDB
            #insert_agtsaver_table(self.db_cursor, self.simid, self.schedule.steps,[x for x in self.schedule.agents if isinstance(x, Saver)])
            #insert_agtloan_table(self.db_cursor, self.simid, self.schedule.steps, [x for x in self.schedule.agents if isinstance(x, Loan)])
            # # It needs to log before the 2nd round effect begin because the function initializes
            insert_agtbank_table(self.db_cursor, self.simid, self.schedule.steps,
                                 [x for x in self.schedule.agents if isinstance(x, Bank)])
            # insert_agtibloan_table(self.db_cursor, self.simid, self.schedule.steps,
            #                        [x for x in self.schedule.agents if isinstance(x, Ibloan)])
            self.conn.commit()

        self.schedule.step()
        self.datacollector.collect(self)

    def run_model(self, step_count=20):
        """
        This method is only avail in the command mode
        :param step_count:
        :return:
        """
        for i in range(step_count):
            if i % 10 == 0 or (i+1) == step_count:
                logger.info(" STEP: %3d - # of sovent bank: %2d", i, len([x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent]))
            try:
                self.step()
            except:
                error = traceback.format_exc()
                logger.error(error)
            if len([x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent]) == 0:
                logger.info("All banks are bankrupt!")
                break
        #df_bank, df_ibloan = convert_result2dataframe(self.lst_bank_ratio, self.lst_ibloan)
        #return df_bank, df_ibloan
        return True
