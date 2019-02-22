from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule, NetworkModule
from mesa.visualization.UserParam import UserSettableParameter

from banksim.model import MesaAbba


def mesa_abba_network_portrayal(G):
    portrayal = dict()
    portrayal['nodes'] = [{'id': node_id,
                           'size': 3,
                           'color': '#CC0000',
                           'label': 'Bank{}'.format(node_id),
                           }
                          for node_id in G.node]

    portrayal['edges'] = [{'id': edge_id,
                           'source': source,
                           'target': target,
                           'color': '#000000',
                           }
                          for edge_id, (source, target) in enumerate(G.edges)]

    return portrayal


canvas_network = NetworkModule(mesa_abba_network_portrayal, 500, 600, library='sigma')
chart_element = ChartModule([{"Label":"BankAsset","Color":"#AA0000"}])

model_params = {"initial_saver": UserSettableParameter("slider", "# of Saver", 10000, 10000, 20000, 100),
                "initial_bank": UserSettableParameter("slider", "# of Bank", 10, 10, 20, 1),
                "initial_loan": UserSettableParameter("slider", "# of Loan", 20000, 10000, 30000,100),
                "initial_equity": UserSettableParameter("slider", "Initial Equity of Bank", 100, 100, 200,1),
                "car": UserSettableParameter("slider", "Min capital adequacy ratio", 0.08, 0.01, 0.10, 0.01)}

server = ModularServer(MesaAbba, [canvas_network, chart_element], "ABBA - Banking system simulation", model_params)
server.port = 8521
