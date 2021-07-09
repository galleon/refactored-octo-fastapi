from fastapi import FastAPI, File, Response, UploadFile
from fastapi.responses import StreamingResponse

from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage
from starlette.responses import FileResponse
import tensorflow
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

from PIL import Image

from MRIsegmentation.params import BUCKET_NAME
from MRIsegmentation.utils import tversky, focal_tversky

import io
import numpy as np
import os
import pandas as pd
import tempfile
import urllib.request as ur
import uuid
import zipfile
from base64 import b64encode

# from MRIsegmentation.model import

"""
https://stackoverflow.com/questions/66178227/fast-api-how-to-show-an-image-from-post-in-get
"""

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


def load_unet_model():
    """
    Load UNET model from Google Storage!
    """
    # url = "https://drive.google.com/uc?export=download&confirm=0wi8&id=1-9EorWUxvPrjon6YDqzwl8Zg5os-4aZ9"
    if not os.path.isfile("vgg19_final.h5"):
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob("models/" + f"vgg19_final.h5")
        blob.download_to_filename(f"vgg19_final.h5")

    model = load_model(
        "vgg19_final.h5",
        custom_objects={
            "tversky": tversky,
            "focal_tversky": focal_tversky,
        },
    )
    model.compile(loss=model.loss, optimizer=model.optimizer, metrics=[tversky])

    return model


def load_df():
    """
    Load Dataframe
    """
    return pd.read_csv("gs://galleon-mri/brain_df.csv")


def zipfiles(filenames):
    """
    Create a response made of one zipfile containing all files
    """
    zip_filename = "archive.zip"

    s = io.BytesIO()
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)

        # Add file, at correct path
        zf.write(fpath, fname)

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = Response(
        s.getvalue(),
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment;filename={zip_filename}"},
    )

    return resp


model = load_unet_model()

# define a root `/` endpoint
@app.get("/")
def index():
    return {"ok": True}


@app.get("/patients")
def patients():
    df = load_df()

    list_of_unique_patients = set(df["patient_id"].values)

    return {"patients": list_of_unique_patients}


@app.get("/patients/{patient_id}")
def get_number_of_slices(patient_id: str):
    df = load_df()

    number_of_slices = len(df[df["patient_id"] == patient_id])

    return {"id": patient_id, "number_of_slices": number_of_slices}


@app.get("/patients/{patient_id}/{slice_id}")
def get_images(patient_id: str, slice_id: int):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    # List all files in directory
    # blobs = bucket.list_blobs(prefix=file_id, delimiter=delimiter)

    blob = bucket.blob(f"kaggle_3m/{patient_id}/{patient_id}_{slice_id}.tif")
    blob.download_to_filename(f"{patient_id}_{slice_id}.tif")
    blob = bucket.blob(f"kaggle_3m/{patient_id}/{patient_id}_{slice_id}_mask.tif")
    blob.download_to_filename(f"{patient_id}_{slice_id}_mask.tif")

    return zipfiles(
        [f"{patient_id}_{slice_id}.tif", f"{patient_id}_{slice_id}_mask.tif"]
    )


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # store image locally

    # print(type(file), file, file.filename)

    image = np.array(Image.open(file.file))

    # print(image.shape)
    # print(image)

    image = image / 255
    image = tensorflow.expand_dims(image, axis=0)
    # print(image.shape)

    # predict from image
    mask_p = model.predict(image)[0]

    name = f"{str(uuid.uuid4())}.tiff"

    # print("After predict: ", type(mask_p), mask_p.shape)

    mask_p2 = np.squeeze(mask_p)

    # print("After squeeze: ", type(mask_p2), mask_p2.shape)

    result1 = Image.fromarray(mask_p2 * 255)
    result1.save(name)

    with open(name, "rb") as file:
        byte_content = file.read()

    base64_bytes = b64encode(byte_content)

    base64_string = base64_bytes.decode("utf-8")

    # print(f"base_string: {len(base64_string)} - {base64_string[:20]}")

    # result1.convert("L").save("test1234.png")

    # result2 = Image.open("test1234.tiff")
    # result2.seek(0)

    return {f"{name}": base64_string}
