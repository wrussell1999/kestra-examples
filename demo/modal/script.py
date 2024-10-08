import os
from typing import Tuple

import modal
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

app = modal.App(
    "order-forecast",
    secrets=[
        modal.Secret.from_local_environ(
            env_keys=[
                "CPU",
                "MEMORY",
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
                "AWS_DEFAULT_REGION",
            ]
        )
    ],
)

image = modal.Image.debian_slim().pip_install(
    "pandas",
    "boto3",
    "kestra",
    "pyarrow",
    "plotly",
    "statsmodels",
)


@app.function(image=image, cpu=float(os.getenv("CPU")), memory=int(os.getenv("MEMORY")))
def predict_order_volume(
    forecast_file: str,
    html_report: str,
    s3_bucket: str,
    nr_days_fcst: int,
    dataset_url: str,
    color_history: str,
    color_prediction: str,
) -> Tuple[str, str]:
    import datetime
    import boto3
    from kestra import Kestra
    import pandas as pd
    import plotly.graph_objs as go
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    # ==================== EXTRACT =================
    df = pd.read_parquet(dataset_url)
    initial_nr_rows = len(df)
    print(f"Number of rows in the dataset: {initial_nr_rows}")

    # ==================== TRANSFORM ====================
    # Extract 'ds' (date) from 'ordered_at' and use 'order_total' as 'y'
    df["ds"] = pd.to_datetime(df["ordered_at"]).dt.date
    df = df.groupby("ds").agg({"order_total": "sum"}).reset_index()
    df.rename(columns={"order_total": "y"}, inplace=True)

    # Ensure daily frequency
    df["ds"] = pd.to_datetime(df["ds"])
    df.set_index("ds", inplace=True)
    df = df.asfreq("D", fill_value=0)  # Fill missing days with 0 order totals
    nr_rows_daily = len(df)

    # ==================== TRAIN SARIMA MODEL ====================
    model = SARIMAX(df["y"], order=(1, 1, 1), seasonal_order=(1, 1, 1, 7))
    sarima_fit = model.fit(disp=False)

    # ==================== PREDICT ====================
    future = sarima_fit.get_forecast(steps=nr_days_fcst)
    forecast = future.summary_frame()

    # Create future dates
    future_dates = pd.date_range(
        df.index.max() + datetime.timedelta(days=1), periods=nr_days_fcst
    )
    forecast_df = pd.DataFrame({"ds": future_dates, "yhat": forecast["mean"]})
    forecast_df.to_parquet(forecast_file)

    # ==================== VISUALIZE WITH PLOTLY ====================
    forecast_fig = go.Figure()
    forecast_fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["y"],
            mode="lines",
            name="Historical Order Volume",
            line=dict(color=color_history),
        )
    )
    forecast_fig.add_trace(
        go.Scatter(
            x=forecast_df["ds"],
            y=forecast_df["yhat"],
            mode="lines",
            name="Predicted Order Volume",
            line=dict(color=color_prediction),
        )
    )

    forecast_fig.update_layout(
        title=f"Order Volume Prediction for the Next {nr_days_fcst} Days",
        xaxis_title="Date",
        yaxis_title="Order Total",
        legend_title="Legend",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
    )

    forecast_fig.write_html(html_report)

    # ==================== UPLOAD TO S3 ====================
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION"),
    )
    files_to_upload = [html_report, forecast_file]

    for file_name in files_to_upload:
        s3.upload_file(file_name, s3_bucket, file_name)
        print(f"File {file_name} uploaded to {s3_bucket}.")

    Kestra.outputs(
        dict(
            initial_nr_rows=initial_nr_rows,
            nr_rows_daily=nr_rows_daily,
            forecast_file=forecast_file,
            html_report=html_report,
        )
    )
    return forecast_file, html_report


@app.local_entrypoint()
def generate_and_predict(
    forecast_file: str,
    html_report: str,
    s3_bucket: str,
    nr_days_fcst: int,
    dataset_url: str,
    color_history: str,
    color_prediction: str,
) -> None:
    results = predict_order_volume.remote(
        forecast_file,
        html_report,
        s3_bucket,
        nr_days_fcst,
        dataset_url,
        color_history,
        color_prediction,
    )
    print(f"Forecast file: {results[0]}, HTML report: {results[1]}")
