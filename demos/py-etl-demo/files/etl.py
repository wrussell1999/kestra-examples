import os
import pandas as pd
from kestra import Kestra

df = pd.read_csv(os.environ['DATASET_URL'])
total_revenue = df['total'].sum()
Kestra.outputs({"total": total_revenue})

discount_amount = float(os.environ['DISCOUNTED_AMOUNT'])
if discount_amount > 0:
  df['discounted_total'] = df['total'] * (1 - discount_amount)
  df.to_csv(os.environ['FILENAME'])
