from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule, NetworkModule
from mesa.visualization.UserParam import UserSettableParameter

from banksim.model import BankSim


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

model_params = {"init_db": UserSettableParameter("checkbox",'Initialize DB',value=True),
                "write_db": UserSettableParameter("checkbox",'Write DB',value=True),
                "max_steps": UserSettableParameter("slider", "Max steps", 20, 10, 200, 1),
                "initial_saver": UserSettableParameter("slider", "# of Saver", 10000, 10000, 20000, 100),
                "initial_bank": UserSettableParameter("slider", "# of Bank", 10, 10, 20, 1),
                "initial_loan": UserSettableParameter("slider", "# of Loan", 20000, 10000, 30000,100),
                "initial_equity": UserSettableParameter("slider", "Initial Equity of Bank", 100, 100, 200,1),
                "car": UserSettableParameter("number", "Minimum capital adequacy ratio", value=0.08),
                "rfree": UserSettableParameter("number","Risk Free Rate", value=0.01),
                "min_reserves_ratio": UserSettableParameter("number","Minimum Reserve Ratio", value=0.03)
                }

server = ModularServer(BankSim, [canvas_network, chart_element], "Banking system simulator", model_params)

server.port = 8521
