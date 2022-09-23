"""
사례 1 - 단일 뱅크, 랜덤워크
"""

import mesa
import numpy as np

from mesa.visualization.UserParam import UserSettableParameter


class Bank(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.asset = 100

    def step(self):
        self.asset += np.random.randint(0, 10)


def compute_asset(model):
    return sum([agent.asset for agent in model.schedule.agents])


class ModelBankingSystem(mesa.Model):
    def __init__(self, N, width, height, num_step):
        self.num_agents = N
        self.num_steps = num_step
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.datacollector = mesa.DataCollector(model_reporters={"자산": compute_asset})

        a = Bank(0, self)
        self.schedule.add(a)
        self.grid.place_agent(a, (0, 0))

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

    portrayal = {
        "Shape": "files/logo_bankofkorea.png",
        "scale": 0.9,
        "Layer": 1,
        "Budget": 10,
        "text_color": "red",
    }
    return portrayal


model_params = {
    "N": 1,
    "width": 10,
    "height": 10,
    "num_step": UserSettableParameter("number", "Number of Steps", value=10),
}

grid = mesa.visualization.CanvasGrid(agent_portrayal, 1, 1, 200, 200)
chart = mesa.visualization.ChartModule(
    [{"Label": "자산", "Color": "#0000FF"}], data_collector_name="datacollector"
)
server = mesa.visualization.ModularServer(ModelBankingSystem, [grid, chart], "사례1-은행 시스템", model_params)
server.port = 8521  # The default
server.launch()
