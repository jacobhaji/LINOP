# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

import gurobipy as gp
from gurobipy import GRB

# Definerer alle variable
# Først for månederne
months = ["January", "February", "March", "April", "May", "June"]

oils = ["VEG1", "VEG2", "OIL1", "OIL2", "OIL3"]

PPOO = {
    ('January', 'VEG1'): 110,
    ('January', 'VEG2'): 120,
    ('January', 'OIL1'): 130,
    ('January', 'OIL2'): 110,
    ('January', 'OIL3'): 115,
    ('February', 'VEG1'): 130,
    ('February', 'VEG2'): 130,
    ('February', 'OIL1'): 110,
    ('February', 'OIL2'): 90,
    ('February', 'OIL3'): 115,
    ('March', 'VEG1'): 110,
    ('March', 'VEG2'): 140,
    ('March', 'OIL1'): 130,
    ('March', 'OIL2'): 100,
    ('March', 'OIL3'): 95,
    ('April', 'VEG1'): 120,
    ('April', 'VEG2'): 110,
    ('April', 'OIL1'): 120,
    ('April', 'OIL2'): 120,
    ('April', 'OIL3'): 125,
    ('May', 'VEG1'): 100,
    ('May', 'VEG2'): 120,
    ('May', 'OIL1'): 150,
    ('May', 'OIL2'): 110,
    ('May', 'OIL3'): 105,
    ('June', 'VEG1'): 90,
    ('June', 'VEG2'): 100,
    ('June', 'OIL1'): 140,
    ('June', 'OIL2'): 80,
    ('June', 'OIL3'): 135
}


hardness = {"VEG1": 8.8, "VEG2": 6.1, "OIL1": 2.0, "OIL2": 4.2, "OIL3": 5.0}

final_product_price = 150
start_storage = 500
goal_storage = 500
max_of_VEG = 200
max_of_OIL = 250

min_hardness = 3
max_hardness = 6
cost_of_storing = 5

#Definerer modellen
final_product = gp.Model('Fremstilling af final product')
# Tons af final product produceret hver måned
produced_product = final_product.addVars(months, name="Producering")
# Mængden købt af hver olie i hver måned
buy = final_product.addVars(months, oils, name = "Køb")
# Mængden brugt af hver olie i hver måned
utilize = final_product.addVars(months, oils, name = "Brug")
# Mængden lagret af hver olie i hver periode
storage = final_product.addVars(months, oils, name = "Lager")

#1. Start-lageret defineret
Balance0 = final_product.addConstrs((start_storage + buy[months[0], oil]
                 == utilize[months[0], oil] + storage[months[0], oil]
                 for oil in oils), "Initial_Balance")

#2. Lager defineret
Balance = final_product.addConstrs((storage[months[months.index(month)-1], oil] + buy[month, oil]
                 == utilize[month, oil] + storage[month, oil]
                 for oil in oils for month in months if month != month[0]), "Balance")

#3. Målet for slutlageret defineret
TargetInv = final_product.addConstrs((storage[months[-1], oil] == goal_storage for oil in oils),"End_Balance")

#4 Maksimum af vegetarisk olie constraint
VegCapacity = final_product.addConstrs((gp.quicksum(utilize[month, oil] for oil in oils if "VEG" in oil)
                 <= max_of_VEG for month in months), "Capacity_Veg")

#5 Maksimum af ikke-vegetarisk olie constraint
NonVegCapacity = final_product.addConstrs((gp.quicksum(utilize[month, oil] for oil in oils if "OIL" in oil)
                 <= max_of_OIL for month in months), "Capacity_Oil")

#6. Hardness, skal ligge mellem hardness_min og hardness_max
HardnessMin = final_product.addConstrs((gp.quicksum(hardness[oil]*utilize[month, oil] for oil in oils)
                 >= min_hardness*produced_product[month] for month in months), "Hardness_lower")
HardnessMax = final_product.addConstrs((gp.quicksum(hardness[oil]*utilize[month, oil] for oil in oils)
                 <= max_hardness*produced_product[month] for month in months), "Hardness_upper")

#7. Total tons af olie brugt i hver måned skal være lig total tons af final_product produceret i den måned
MassConservation = final_product.addConstrs((utilize.sum(month) == produced_product[month] for month in months), "Mass_conservation")

#0. Obj. funktion
obj = final_product_price*produced_product.sum() - buy.prod(PPOO) - cost_of_storing*storage.sum()
final_product.setObjective(obj, GRB.MAXIMIZE) # maximize profit

final_product.optimize()

# Definering af en købsplan til firmaet
rows = months.copy()
columns = oils.copy()
purchase_plan = pd.DataFrame(columns=columns, index=rows, data=0.0)

for month, oil in buy.keys():
    if (abs(buy[month, oil].x) > 1e-6):
        purchase_plan.loc[month, oil] = np.round(buy[month, oil].x, 1)
purchase_plan


# Definering af månedlig forbrug af olie til firmaet
rows = months.copy()
columns = oils.copy()
reqs = pd.DataFrame(columns=columns, index=rows, data=0.0)

for month, oil in utilize.keys():
    if (abs(utilize[month, oil].x) > 1e-6):
        reqs.loc[month, oil] = np.round(utilize[month, oil].x, 1)
reqs

# Definering af planen for lageret for hver måneden til firmaet
rows = months.copy()
columns = oils.copy()
storage_plan = pd.DataFrame(columns=columns, index=rows, data=0.0)

for month, oil in storage.keys():
    if (abs(storage[month, oil].x) > 1e-6):
        storage_plan.loc[month, oil] = np.round(storage[month, oil].x, 1)
storage_plan
