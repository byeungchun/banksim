from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.UserParam import UserSettableParameter

from mesaabba.agents import Saver,Ibloan,Loan,Bank
from mesaabba.model import MesaAbba


def mesa_abba_portrayal(agent):
    if agent is None:
        return

    portrayal = {}

    if isinstance(agent,Saver):
        portrayal["Shape"] = "circle"
        portrayal["r"] = .5
        portrayal["Layer"] = 1
        portrayal["Filled"] = "true"
        portrayal["Color"] = "#3349FF"

    # elif type(agent) is Ibloan:
    #     portrayal["Shape"] = "star"
    #     portrayal["r"] = .5
    #     portrayal["Layer"] = 2
    #     portrayal["Filled"] = "true"
    #
    # elif type(agent) is Loan:
    #     portrayal["Shape"] = "rectangle"
    #     portrayal["r"] = .5
    #     portrayal["Layer"] = 3
    #     portrayal["Filled"] = "true"

    elif isinstance(agent, Bank):
        portrayal["Shape"] = "rect"
        portrayal["w"] = .5
        portrayal["h"] = .5
        portrayal["Layer"] = 1
        portrayal["Filled"] = "true"
        portrayal["Color"] = "#FF3C33"

    return portrayal


canvas_element = CanvasGrid(mesa_abba_portrayal,20,20,500,500)
chart_element = ChartModule([{"Label":"Saver","Color":"#AA0000"},
                             {"Label":"Bank", "Color": "#666666"}])

model_params = {"initial_saver": UserSettableParameter("slider", "Initial Saver", 100, 1, 200)}

server = ModularServer(MesaAbba, [canvas_element, chart_element], "Mesa ABBA model", model_params)
server.port = 8521