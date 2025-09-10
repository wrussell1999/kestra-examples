import pandas as pd

df = pd.read_csv("https://huggingface.co/datasets/kestra/datasets/raw/main/csv/orders.csv")
total_revenue = df['total'].sum()
print(total_revenue)