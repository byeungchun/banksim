"""
사례 4 - 단일 뱅크, 예금자, 대출
"""

import mesa
import numpy as np

from mesa.visualization.UserParam import UserSettableParameter


class Saver(mesa.Agent):
    def __init__(self, unique_id, pos, model, money):
        super().__init__(unique_id, pos)
        self.money = money

    def step(self):
        self.money += self.money * 0.03


class Loan(mesa.Agent):
    def __init__(self, unique_id, pos, model, loan):
        super().__init__(unique_id, pos)
        self.loan = loan

    def step(self):
        pass


class Bank(mesa.Agent):
    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, pos)
        self.model = model
        self.asset = 100

    def step(self):
        for agent in self.model.schedule.agents:
            if type(agent) is Saver:
                self.asset -= agent.money * 0.03
            if type(agent) is Loan:
                self.asset += agent.loan * 0.04


def compute_saver_money(model):
    return sum([agent.money for agent in model.schedule.agents if type(agent) is Saver])


def compute_bank_asset(model):
    return sum([agent.asset for agent in model.schedule.agents if type(agent) is Bank])


def compute_loan_total(model):
    return sum([agent.loan for agent in model.schedule.agents if type(agent) is Loan])


class ModelBankingSystem(mesa.Model):
    def __init__(
        self,
        height=10,
        width=10,
        initial_bank=1,
        initial_savers=8,
        initial_loans=10,
        num_step=10,
    ):
        super().__init__()
        self.width = width
        self.height = height
        self.initial_bank = initial_bank
        self.initial_savers = initial_savers
        self.initial_loans = initial_loans
        self.num_steps = num_step

        self.grid = mesa.space.MultiGrid(self.width, self.height, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "BankAsset": compute_bank_asset,
                "SaverMoney": compute_saver_money,
                "LoanTotal": compute_loan_total,
            }
        )
        self.lst_pos = []

        x = int(self.width / 2)
        y = int(self.height / 2)
        bank = Bank(self.next_id(), (x, y), self)
        self.grid.place_agent(bank, (x, y))
        self.schedule.add(bank)
        self.lst_pos.append((x, y))

        for i in range(initial_savers):
            pos = self._find_empty_pos()
            saver = Saver(self.next_id(), pos, self, 10)
            self.grid.place_agent(saver, pos)
            self.schedule.add(saver)

        for i in range(initial_loans):
            pos = self._find_empty_pos()
            loan = Loan(self.next_id(), pos, self, 10)
            self.grid.place_agent(loan, pos)
            self.schedule.add(loan)

        self.running = True
        self.datacollector.collect(self)

    def _find_empty_pos(self):
        for _ in range(self.width * self.height):
            pos = (
                self.random.randrange(self.width),
                self.random.randrange(self.height),
            )
            if pos not in self.lst_pos:
                self.lst_pos.append(pos)
                return pos
        print("There is no empty cell. Check width/height size")

        return False

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

        if self.schedule.steps == self.num_steps:
            self.running = False

    def run_model(self, n):
        for i in range(n):
            self.step()


def agent_portrayal(agent):

    if type(agent) is Bank:
        portrayal = {
            "Shape": "files/logo_bankofkorea.png",
            "scale": 0.9,
            "Layer": 1,
            "Budget": agent.asset,
            "text_color": "red",
        }

    if type(agent) is Saver:
        portrayal = {
            "Shape": "files/saver.png",
            "scale": 0.9,
            "Layer": 1,
            "Budget": agent.money,
            "text_color": "red",
        }

    if type(agent) is Loan:
        portrayal = {
            "Shape": "files/loan.png",
            "scale": 0.9,
            "Layer": 1,
            "Budget": agent.loan,
            "text_color": "red",
        }

    return portrayal


height = 5
width = 5

initial_bank = 1
initial_savers = 8
initial_loans = 10

model_params = {
    "width": width,
    "height": height,
    "initial_bank": initial_bank,
    "initial_savers": initial_savers,
    "initial_loans": initial_loans,
    "num_step": UserSettableParameter("number", "Number of Steps", value=10),
}

grid = mesa.visualization.CanvasGrid(agent_portrayal, width, height, 400, 400)
chart = mesa.visualization.ChartModule(
    [
        {"Label": "BankAsset", "Color": "#0000FF"},
        {"Label": "SaverMoney", "Color": "#FF0000"},
        {"Label": "LoanTotal", "Color": "#00FF00"},
    ]
)

server = mesa.visualization.ModularServer(
    ModelBankingSystem,
    [grid, chart],
    "사례 4 - 단일 뱅크, 예금자(8)-이자(3%), 대출(10)-이자(4%) ",
    model_params,
)
server.port = 8521  # The default
server.launch()
