from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule, NetworkModule
from mesa.visualization.UserParam import UserSettableParameter

from mesaabba.model import MesaAbba


def mesa_abba_network_portrayal(G):
    portrayal = dict()
    portrayal['nodes'] = [{'id': node_id,
                           'size': 3 if agents else 1,
                           'color': '#CC0000',
                           'label': None if not agents else 'Agent:{}'.format(agents[0].unique_id),
                           }
                          for (node_id, agents) in G.nodes.data('agent')]

    portrayal['edges'] = [{'id': edge_id,
                           'source': source,
                           'target': target,
                           'color': '#000000',
                           }
                          for edge_id, (source, target) in enumerate(G.edges)]

    return portrayal


canvas_network = NetworkModule(mesa_abba_network_portrayal, 500, 500, library='sigma')
chart_element = ChartModule([{"Label":"Saver","Color":"#AA0000"},
                             {"Label":"Bank", "Color": "#666666"}])

model_params = {"initial_saver": UserSettableParameter("slider", "Initial Saver", 100, 1, 200)}

server = ModularServer(MesaAbba, [canvas_network, chart_element], "Mesa ABBA model", model_params)
server.port = 8521