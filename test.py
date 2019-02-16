import pandas as pd
from mesaabba.model import MesaAbba

model = MesaAbba()
res = model.run_model()

df = pd.DataFrame(res)
