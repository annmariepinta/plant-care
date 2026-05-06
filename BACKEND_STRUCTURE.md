# Backend Structure for Tomato Disease Detection

This document describes the recommended backend structure for serving your Keras (.h5) model and providing disease detection and treatment info via a REST API.

---

## Directory Structure

```
backend/
│
├── app.py                # Main API entry point
├── model/
│   └── tomato_disease_model.h5
├── requirements.txt      # Python dependencies
├── utils/
│   └── predict.py        # Image preprocessing & prediction logic
└── treatment_data/
    └── treatments.json   # (Optional) Static treatment info
```

---

## Key Components

### 1. app.py (API entry)
- Exposes endpoints:
  - `/predict` (POST): Accepts image, returns predicted class & confidence.
  - `/treatment/<disease>` (GET): Returns treatment info for a disease.

### 2. model/tomato_disease_model.h5
- Your trained Keras model.

### 3. utils/predict.py
- Loads the model once at startup.
- Handles image preprocessing (resize, normalize).
- Runs prediction and returns class name & confidence.

### 4. requirements.txt
- Example:
  ```
  fastapi
  uvicorn
  tensorflow
  pillow
  numpy
  python-multipart
  ```

### 5. treatment_data/treatments.json (Optional)
- Store disease-to-treatment mappings for fast lookup.

---

## Example: FastAPI app.py

```python
from fastapi import FastAPI, File, UploadFile
from utils.predict import predict_image
import uvicorn
import json

app = FastAPI()

# Load treatment data if using static JSON
with open('treatment_data/treatments.json') as f:
    TREATMENTS = json.load(f)

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    result = predict_image(contents)
    return result

@app.get("/treatment/{disease}")
def get_treatment(disease: str):
    return TREATMENTS.get(disease.lower(), {"error": "No treatment info found"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Example: utils/predict.py

```python
import numpy as np
from PIL import Image
import io
import tensorflow as tf

MODEL = tf.keras.models.load_model('model/tomato_disease_model.h5')
CLASS_NAMES = ["Early Blight", "Healthy Tomato Leaf", "Late Blight", "Leaf Mold", "Non-Tomato Leaf"]

def predict_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((224, 224))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    preds = MODEL.predict(img_array)
    class_id = np.argmax(preds)
    confidence = float(np.max(preds))
    return {
        "class": CLASS_NAMES[class_id],
        "confidence": confidence
    }
```

---

## Local Backend Environment

Create and use a virtual environment from the project root:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
cd backend
uvicorn app:app --reload
```

The backend environment uses pinned TensorFlow-compatible versions for the model runtime:

```text
tensorflow==2.16.2
numpy==1.26.4
opencv-python==4.10.0.84
```

The backend maps model output indexes in this order:

```text
0 = Early Blight
1 = Healthy Tomato Leaf
2 = Late Blight
3 = Leaf Mold
4 = Non-Tomato Leaf
```

Images are normalized with `image / 255.0` by default. You can override this with `MODEL_PREPROCESSING`, but it should match the preprocessing used during training.

Visual disease calibration is disabled by default so leaf images are classified by the trained model output order. It can be enabled for experiments with `APPLY_VISUAL_DISEASE_CALIBRATION=true`, but keep it off for normal testing.

## Steps to Deploy

1. Place your `.h5` model in `model/`.
2. Implement the API as above.
3. Add treatment info as needed.
4. Create and activate the backend virtual environment.
5. Install dependencies: `python -m pip install -r backend\requirements.txt`
6. Run from `backend/`: `uvicorn app:app --reload`

---

Let me know if you want a ready-to-use template or help with any part of this setup!
