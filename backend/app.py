import json
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from utils.predict import (
    APPLY_VISUAL_DISEASE_CALIBRATION,
    CLASS_NAMES,
    PREPROCESSING_MODE,
    normalize_prediction_profile,
    predict_image,
    predict_image_regions,
)


BASE_DIR = Path(__file__).resolve().parent
TREATMENT_FILE = BASE_DIR / "treatment_data" / "treatments.json"

app = FastAPI(
    title="Tomato Disease Detection API",
    description="Serves tomato leaf disease predictions from a Keras model.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_treatments():
    if not TREATMENT_FILE.exists():
        return {}

    with TREATMENT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("_", "-").replace(" ", "-")


TREATMENTS = _load_treatments()


@app.get("/")
def health_check():
    return {"status": "ok", "service": "tomato-disease-detection"}


@app.get("/model-info")
def model_info():
    return {
        "class_names": [
            {"index": index, "name": name}
            for index, name in enumerate(CLASS_NAMES)
        ],
        "preprocessing_mode": PREPROCESSING_MODE,
        "visual_disease_calibration_enabled": APPLY_VISUAL_DISEASE_CALIBRATION,
        "prediction_profiles": ["fast", "balanced"],
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        return predict_image(contents)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Prediction failed.") from error


@app.post("/predict-regions")
async def predict_regions(
    file: UploadFile = File(...),
    profile: str = Query("balanced", pattern="^(fast|balanced)$"),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        return predict_image_regions(contents, profile=normalize_prediction_profile(profile))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Region prediction failed.") from error


@app.get("/treatment/{disease}")
def get_treatment(disease: str):
    key = _normalize_key(disease)
    treatment = TREATMENTS.get(key)

    if treatment is None:
        raise HTTPException(status_code=404, detail="No treatment info found.")

    return treatment
