import pandas as pd
import mesaabba.model

mesamodel = mesaabba.model.MesaAbba()
res = mesamodel.run_model(200)
res.to_csv(r'e:\data\abba\mesatest_res.csv')


# NETLOGO result
with open(r'e:/data/abba/netlogo_bank_ratios_all.csv', 'r') as fin:
    lines = fin.read().splitlines()
df_netlogo = pd.DataFrame([x.split(',') for x in lines[1:]]).iloc[:,1:]
df_netlogo.columns = lines[0].split(',')[1:]

# MESA result
with open(r'e:/data/abba/mesatest_res.csv','r') as fin:
    lines = fin.read().splitlines()
df_mesa = pd.DataFrame([x.split(',') for x in lines[1:]]).iloc[:,1:]
df_mesa.columns = df_netlogo.columns
df_mesa['credit-failure-indicator'] = df_mesa['credit-failure-indicator'].apply(lambda x: 1 if x else 0)
df_mesa['liquidity-failure-indicator'] = df_mesa['liquidity-failure-indicator'].apply(lambda x: 1 if x else 0)

# Comparing values
df_netlogo = df_netlogo.iloc[:1000,:]
df_diff = df_netlogo.astype(float) - df_mesa.astype(float)
df_diff.to_csv(r'e:\data\abba\diff.csv')
