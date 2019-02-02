from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

from mesaabba.agents import Saver, Ibloan, Loan, Bank


def get_num_agents(model):
    return len([a for a in model.schedule.agents])


class MesaAbba(Model):

    height = 20
    width = 20

    initial_saver = 100
    initial_ibloan = 10
    initial_loan = 50
    initial_bank = 50

    def __init__(self, height=20, width=20, initial_saver=100, initial_ibloan=10, initial_loan=50, initial_bank=50):
        super().__init__()
        self.height = height
        self.width = width
        self.initial_saver = initial_saver
        self.initial_ibloan = initial_ibloan
        self.initial_loan = initial_loan
        self.initial_bank = initial_bank

        self.grid = MultiGrid(self.width, self.height, torus=True)
        self.schedule = RandomActivation(self)
        self.datacollector = DataCollector({
            "Saver": get_num_agents,
            "Bank": get_num_agents
        })

        for i in range(self.initial_saver):
            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)
            saver = Saver(self.next_id(), self)
            self.grid.place_agent(saver, (x, y))
            self.schedule.add(saver)

        for i in range(self.initial_ibloan):
            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)
            ibloan = Ibloan(self.next_id(), self)
            self.grid.place_agent(ibloan, (x, y))
            self.schedule.add(ibloan)

        for i in range(self.initial_loan):
            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)
            loan = Loan(self.next_id(), self)
            self.grid.place_agent(loan, (x, y))
            self.schedule.add(loan)

        for i in range(self.initial_bank):
            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)
            bank = Bank(self.next_id(), self)
            self.grid.place_agent(bank, (x, y))
            self.schedule.add(bank)

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

    def run_model(self, step_count=200):

        for i in range(step_count):
            self.step()
