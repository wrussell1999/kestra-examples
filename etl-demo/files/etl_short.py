import os
import pandas as pd
from kestra import Kestra

df = pd.read_csv(os.environ['DATASET'])
total_revenue = df['total'].sum()
Kestra.outputs({"total": total_revenue})
