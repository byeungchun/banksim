"""
사례 2 - 멀티 뱅크, 랜덤워크
"""

import mesa
import numpy as np

from mesa.visualization.UserParam import UserSettableParameter


class Bank(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.asset = 100

    def step(self):
        self.asset += np.random.randint(-20, 20)


def compute_gap(model):
    arr_asset = [agent.asset for agent in model.schedule.agents]

    gap_value = np.max(arr_asset) - np.min(arr_asset)
    print('asset_gap', gap_value)
    # return np.sum(gap)
    return int(gap_value)


def compute_asset(model):
    return sum([agent.asset for agent in model.schedule.agents])


class ModelBankingSystem(mesa.Model):
    def __init__(self, N, width, height, num_step):
        super().__init__()
        self.num_agents = N
        self.num_steps = num_step
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "TotalAsset": compute_asset ,
                "AssetGap": compute_gap
            }
        )

        for i in range(self.num_agents):
            a = Bank(i, self)
            self.schedule.add(a)
            self.grid.place_agent(a, (i, i))

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
        "Budget": agent.asset,
        "text_color": "red",
    }
    return portrayal


model_params = {
    "N": 2,
    "width": 10,
    "height": 10,
    "num_step": UserSettableParameter("number", "Number of Steps", value=10),
}

grid = mesa.visualization.CanvasGrid(agent_portrayal, 2, 2, 200, 200)
chart = mesa.visualization.ChartModule(
    [{"Label": "TotalAsset", "Color": "#0000FF"}, {"Label": "AssetGap", "Color": "#FF0000"}]
)

server = mesa.visualization.ModularServer(ModelBankingSystem, [grid, chart], "사례 2 - 멀티 뱅크, 랜덤워크", model_params)
server.port = 8521  # The default
server.launch()
