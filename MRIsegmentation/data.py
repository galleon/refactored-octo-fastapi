import pandas as pd
import numpy as np


from sklearn.model_selection import train_test_split
from google.cloud import storage

from MRIsegmentation.params import BUCKET_NAME, BUCKET_DATA_PATH


def get_data():
    """returns a DataFrame with nrows from s3 bucket"""
    blob_list = list_blobs(f"gs://{BUCKET_NAME}/{BUCKET_DATA_PATH}")

    # df = pd.read_csv(f"gs://{BUCKET_NAME}/{BUCKET_DATA_PATH}", nrows=nrows)
    print(blob_list)

    df = []

    return df


def holdout(df, train_ratio=0.8, test_to_val_ratio=0.5, include_all=False):

    img_paths = df["image_path"].values
    msk_paths = df["mask_path"].values

    df_mask = df.copy()
    if include_all == False:
        df_mask = df[df["mask"] == 1]

    df_train, df_val = train_test_split(df_mask, train_size=train_ratio)
    df_test, df_val = train_test_split(df_val, test_size=test_to_val_ratio)

    ds_train = tf.data.Dataset.from_tensor_slices(
        (df_train["image_path"].values, df_train["mask_path"].values)
    )
    ds_val = tf.data.Dataset.from_tensor_slices(
        (df_val["image_path"].values, df_val["mask_path"].values)
    )
    ds_test = tf.data.Dataset.from_tensor_slices(
        (df_test["image_path"].values, df_test["mask_path"].values)
    )

    return ds_train, ds_val, ds_test
