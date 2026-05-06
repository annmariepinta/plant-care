# Plant Care App – Current Architecture & Refactor Plan

## 1. Current State

### Frontend
- **Framework:** React (Vite, Tailwind CSS)
- **Detection Flow:**
  1. User uploads a tomato leaf image.
  2. Image is sent directly to the [plant.id](https://plant.id) API using axios.
  3. API returns:
     - Disease prediction (class, probability, description, etc.)
     - Treatment recommendations (biological, chemical, prevention)
  4. Frontend displays the results.

- **Key Files:**
  - `src/pages/detect/index.jsx`: Main detection logic and UI.
  - `src/components/ImageUploader.jsx`: Handles image selection and upload.

### API Usage
- **Endpoint:** `https://plant.id/api/v3/health_assessment`
- **Request:** `POST` with image file in form-data, API key in headers.
- **Response:** JSON with disease predictions and treatment details.

### Data Flow
- **Detection:** Handled by the external API.
- **Treatment:** Also provided by the API response.

---

## 2. Refactor Plan: Move Detection to Backend

### Goal
- Move detection (image classification) to your own backend (using your ML model).
- Use the API (or your own DB) only for treatment info.

### Steps
1. **Frontend:**
   - Change detection endpoint from plant.id API to your backend service.
   - Upload image to your backend.
   - Backend returns predicted disease class (and optionally confidence).
   - Frontend fetches treatment info (from your backend or plant.id API) based on the predicted class.

2. **Backend Service:**
   - Expose an endpoint (e.g., `/api/detect`) that accepts an image and returns the predicted disease.
   - Use your ML model (e.g., from `tomato_disease_project.py`) for prediction.
   - Optionally, expose another endpoint (e.g., `/api/treatment/:disease`) to return treatment info for a given disease.

3. **Treatment Data:**
   - Store treatment info in your backend (DB or static JSON), or
   - Fetch treatment info from plant.id or another API, but only for treatment (not detection).

---

## 3. Example Data Flow After Refactor

1. User uploads image → Frontend sends image to your backend (`/api/detect`).
2. Backend returns disease prediction (e.g., "Early Blight").
3. Frontend requests treatment info for "Early Blight" from your backend (`/api/treatment/early-blight`).
4. Frontend displays prediction and treatment info.

---

## 4. Next Steps
- Build a backend service (Flask, FastAPI, Node.js, etc.) to serve your ML model.
- Update the frontend to use your backend for detection.
- Decide how to serve treatment info (static, DB, or API).

---

Let me know if you want a sample backend structure or code to get started!
