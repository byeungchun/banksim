"""
The full code should now look like:
"""

import mesa


class MoneyAgent(mesa.Agent):
    """An agent with fixed initial wealth."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = 1

    def step(self):
        # The agent's step will go here.
        # For demonstration purposes we will print the agent's unique_id
        print("Hi, I am agent " + str(self.unique_id) + ".")


class MoneyModel(mesa.Model):
    """A model with some number of agents."""

    def __init__(self, N, width, height):
        self.num_agents = N
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        # Create agents
        for i in range(self.num_agents):
            a = MoneyAgent(i, self)
            self.schedule.add(a)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
        self.running = True

    def step(self):
        """Advance the model by one step."""
        self.schedule.step()

    def run_model(self, n):
        for i in range(n):
            self.step()


def agent_portrayal(agent):

    # portrayal = {
    #     "Shape": "circle",
    #     "Filled": "true",
    #     "Layer": 0,
    #     "Color": "red",
    #     "r": 0.5,
    # }

    # return portrayal

    if agent is None:
        return

    portrayal = {}
    if type(agent) == MoneyAgent:
        portrayal = {
            "Shape": "circle",
            "Filled": "true",
            "Layer": 0,
            "Budget": 10,
            "Color": "red",
            "r": 0.5,
        }

    return portrayal


model_params = {
    "N": mesa.visualization.Slider(
        "Number of agents",
        100,
        2,
        200,
        1,
        description="Choose how many agents to include in the model",
    ),
    "width": 10,
    "height": 10,
}

grid = mesa.visualization.CanvasGrid(agent_portrayal, 10, 10, 500, 500)
# server = mesa.visualization.ModularServer(
#     MoneyModel, [grid], "Money Model", {"N": 100, "width": 10, "height": 10}
# )
server = mesa.visualization.ModularServer(
    MoneyModel, [grid], "Money Model", model_params
)
server.port = 8521  # The default
server.launch()
