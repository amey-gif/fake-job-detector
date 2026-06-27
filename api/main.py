from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import re
import numpy as np
import scipy.sparse as sp
import shap
from fastapi import Request
from fastapi.responses import JSONResponse


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/predict")
async def options_predict(request: Request):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

model = joblib.load("../model/model.pkl")
tfidf = joblib.load("../model/tfidf.pkl")
encoders = joblib.load("../model/encoders.pkl")
explainer = shap.TreeExplainer(model)

tfidf_features = tfidf.get_feature_names_out().tolist()
meta_feature_names = ['telecommuting', 'has_company_logo', 'has_questions',
                      'employment_type_enc', 'required_experience_enc', 'salary_missing']
all_features = tfidf_features + meta_feature_names

class JobPosting(BaseModel):
    title: str = ""
    company_profile: str = ""
    description: str = ""
    requirements: str = ""
    benefits: str = ""
    telecommuting: int = 0
    has_company_logo: int = 0
    has_questions: int = 0
    employment_type: str = "unknown"
    required_experience: str = "unknown"
    has_salary: int = 0
    has_emojis: int = 0


def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

@app.get("/")
def root():
    return {"status": "Fake Job Detector API is running"}

@app.post("/predict")
def predict(job: JobPosting):
    combined = f"{job.title} {job.company_profile} {job.description} {job.requirements} {job.benefits}"
    cleaned = clean_text(combined)
    X_text = tfidf.transform([cleaned])

    le_emp = encoders['employment_type']
    le_exp = encoders['required_experience']

    emp_type = job.employment_type if job.employment_type in le_emp.classes_ else 'unknown'
    exp_type = job.required_experience if job.required_experience in le_exp.classes_ else 'unknown'

    meta = np.array([[
        job.telecommuting,
        job.has_company_logo,
        job.has_questions,
        le_emp.transform([emp_type])[0],
        le_exp.transform([exp_type])[0],
        1 - job.has_salary
    ]])

    X_meta = sp.csr_matrix(meta)
    X_final = sp.hstack([X_text, X_meta])

    prob = model.predict_proba(X_final)[0][1]

    india_scam_keywords = [
    "registration fee", "send aadhaar", "wire transfer",
    "placement support", "google form", "no stipend",
    "earn from home", "part time earn", "data entry work from home",
    "responses managed off linkedin", "certificate provided",
    "100% placement", "work from home earn"
    ]

    combined_lower = combined.lower()
    keyword_hits = sum(1 for kw in india_scam_keywords if kw in combined_lower)
    boost = keyword_hits * 0.15

    if job.has_emojis:
        boost += 0.10

    prob = min(1.0, prob + boost)


    verdict = "FAKE" if prob >= 0.5 else "REAL"

    shap_vals = explainer.shap_values(X_final)
    shap_array = np.array(shap_vals).flatten()
    top_indices = np.argsort(np.abs(shap_array))[::-1][:5]
    top_reasons = [
        {"feature": all_features[i], "impact": round(float(shap_array[i]),4)}
        for i in top_indices
    ]

    return {
    "verdict": verdict,
    "fake_probability": round(float(prob), 4),
    "keyword_hits": keyword_hits,
    "boost": round(boost, 4),
    "has_emojis": job.has_emojis,
    "top_reasons": top_reasons
    }