"""
사례 3 - 단일 뱅크, 저축고객
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


class Bank(mesa.Agent):
    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, pos)
        self.model = model
        self.asset = 100

    def step(self):
        for saver in self.model.schedule.agents:
            if type(saver) is Saver:
                self.asset -= saver.money * 0.03


def compute_saver_money(model):
    return sum([agent.money for agent in model.schedule.agents if type(agent) is Saver])


def compute_bank_asset(model):
    return sum([agent.asset for agent in model.schedule.agents if type(agent) is Bank])


class ModelBankingSystem(mesa.Model):
    def __init__(
        self, height=10, width=10, initial_bank=1, initial_savers=8, num_step=10
    ):
        super().__init__()
        self.width = width
        self.height = height
        self.initial_bank = initial_bank
        self.initial_savers = initial_savers
        self.num_steps = num_step

        self.grid = mesa.space.MultiGrid(self.width, self.height, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "BankAsset": compute_bank_asset,
                "SaverMoney": compute_saver_money,
            }
        )

        x = int(self.width / 2)
        y = int(self.height / 2)
        bank = Bank(self.next_id(), (x, y), self)
        self.grid.place_agent(bank, (x, y))
        self.schedule.add(bank)

        saver_cnt = 0
        for xi in [-1, 0, 1]:
            for yi in [-1, 0, 1]:
                if xi == 0 and yi == 0:
                    continue
                posx = x + xi
                posy = y + yi
                # print(f"saver ({saver_cnt}) - x,y: {(x,y)}, pos: {(posx,posy)} ")
                saver = Saver(self.next_id(), (posx, posy), self, 10)
                self.schedule.add(saver)
                self.grid.place_agent(saver, (posx, posy))
                saver_cnt += 1

        self.running = True
        self.datacollector.collect(self)

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

    return portrayal


height = 5
width = 5

initial_bank = 1
initial_savers = 8

model_params = {
    "width": width,
    "height": height,
    "initial_bank": initial_bank,
    "initial_savers": initial_savers,
    "num_step": UserSettableParameter("number", "Number of Steps", value=10),
}

grid = mesa.visualization.CanvasGrid(agent_portrayal, width, height, 400, 400)
chart = mesa.visualization.ChartModule(
    [
        {"Label": "BankAsset", "Color": "#0000FF"},
        {"Label": "SaverMoney", "Color": "#FF0000"},
    ]
)

server = mesa.visualization.ModularServer(
    ModelBankingSystem, [grid, chart], "사례 3 - 단일 뱅크, 예금자 8명", model_params
)
server.port = 8521  # The default
server.launch()
