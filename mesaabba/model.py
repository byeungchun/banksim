from mesa import Model
from mesa.space import MultiGrid, NetworkGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

import networkx as nx

from mesaabba.agents import Saver, Ibloan, Loan, Bank


def get_num_agents(model):
    return len([a for a in model.schedule.agents])


class MesaAbba(Model):
    height = None
    width = None

    initial_saver = None
    initial_ibloan = None
    initial_loan = None
    initial_bank = None

    rfree = None  # risk free rate
    car = None  # Capital ratio
    libor_rate = None

    def __init__(self, height=20, width=20, initial_saver=10000, initial_ibloan=10, initial_loan=50, initial_bank=10,
                 rfree=0.01, car=0.08):
        super().__init__()
        self.height = height
        self.width = width
        self.initial_saver = initial_saver
        self.initial_ibloan = initial_ibloan
        self.initial_loan = initial_loan
        self.initial_bank = initial_bank
        self.rfree = rfree
        self.reserve_rates = rfree / 2.0  # set reserve rates one half of risk free rate
        self.libor_rate = rfree
        self.bankrupt_liquidation = 1  # 1: it is fire sale of assets, 0: bank liquidates loans at face value
        self.car = car

        #self.grid = MultiGrid(self.width, self.height, torus=True)
        self.G = nx.complete_graph(self.initial_bank)
        self.grid = NetworkGrid(self.G)
        self.schedule = RandomActivation(self)
        self.datacollector = DataCollector({
            "Saver": get_num_agents,
            "Bank": get_num_agents
        })

        for i in range(self.initial_bank):
            bank = Bank(self.next_id(), self, rfree=self.rfree, car=self.car)
            self.grid.place_agent(bank, i)
            self.schedule.add(bank)

        for i in range(self.initial_saver):
            saver = Saver(self.next_id(), self)
            self.grid.place_agent(saver, i % 10)
            self.schedule.add(saver)

        for i in range(self.initial_ibloan):
            ibloan = Ibloan(self.next_id(), self,libor_rate=self.libor_rate)
            #self.grid.place_agent(ibloan, i % 10)
            self.schedule.add(ibloan)

        for i in range(self.initial_loan):
            loan = Loan(self.next_id(), self, rfree=self.rfree)
            #self.grid.place_agent(loan, i % 10)
            self.schedule.add(loan)

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

    def run_model(self, step_count=200):

        for i in range(step_count):
            self.step()
