from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi import HTTPException
from supabase import create_client
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

supabase_admin = create_client(SUPABASE_URL, SERVICE_KEY)
supabase_auth = create_client(SUPABASE_URL, ANON_KEY)
app = FastAPI()

# Serve IMG directory (images)
app.mount("/IMG", StaticFiles(directory="IMG"), name="IMG")

# ---------- ROUTES FOR HTML PAGES ---------- #

@app.get("/")
def serve_index():
    return FileResponse("index.html")


@app.get("/login")
def serve_login():
    return FileResponse("login.html")

@app.get("/reflection")
def serve_login():
    return FileResponse("reflection.html")

@app.get("/setup")
def serve_login():
    return FileResponse("onboard.html")


@app.get("/register")
def serve_register():
    return FileResponse("register.html")


@app.get("/home")
def serve_home():
    return FileResponse("home.html")


class SignupData(BaseModel):
    email: str
    password: str

@app.post("/api/register")
def register(data: SignupData):
    try:
        result = supabase_admin.auth.sign_up({
            "email": data.email,
            "password": data.password
        })

        if result.user is None:
            raise HTTPException(status_code=400, detail="Signup failed")

        user_id = result.user.id  # UUID

        supabase_admin.table("profiles").insert({
            "id": user_id
        }).execute()


        return {"success": True, "user_id": user_id}

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
    
class LoginData(BaseModel):
    email: str
    password: str

@app.post("/api/login")
def login(data: LoginData):
    try:
        result = supabase_auth.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        if result.user is None:
            return {
                "success": False,
                "message": "Invalid email or password"
            }

        return {
            "success": True,
            "user_id": result.user.id
    
        }

    except Exception as e:
        print("LOGIN ERROR:", e)
        return {
            "success": False,
            "message": str(e)
        }
    
class OnboardingData(BaseModel):
    name: str
    weight: float
    height: float
    dob: str
    goal: str
    dietaryPreference: str

@app.post("/predict-meals")
def predict_meals(data: OnboardingData):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        prompt = f"""
You are a nutrition assistant. Based on the following user profile:

Weight: {data.weight} kg
Height: {data.height} cm
Date of Birth: {data.dob}

Dietary Preference: {data.dietaryPreference}

Generate a list of EXACTLY 10 foods that this person is likely to eat regularly.
Foods should be culturally relevant to India unless the dietary preference suggests otherwise.
Try to only include foods which which user would eat on a daily basis.
For each food, include:
- name
- a short description containing main ingredients
- estimated calories per serving

Return ONLY a JSON array.
NO explanation.
NO markdown.
NO code fences.
NO text before or after the JSON.

Example format:
[
  {{"name": "Dal Chawal", "calories": 420, "description": "A traditional Indian meal consisting of lentil curry (dal) served with steamed rice (chawal)."}},
  {{"name": "Roti Aloo Sabzi", "calories": 350, "description": "Whole wheat flatbread with spiced potato curry."}}
]
"""

        response = model.generate_content(prompt)
        raw = response.text.strip()

        print("RAW GEMINI OUTPUT >>>", repr(raw))

        # --- CLEAN CODE FENCES & MARKDOWN ---
        cleaned = (
            raw.replace("```json", "")
               .replace("```JSON", "")
               .replace("``` json", "")
               .replace("```", "")
               .strip()
        )

        # --- EXTRACT JSON ARRAY SAFELY ---
        import re, json
        match = re.search(r'.*', cleaned, re.DOTALL)
        if not match:
            raise ValueError("No JSON array found in Gemini output")

        json_text = match.group(0)
        meals = json.loads(json_text)

        return {
            "success": True,
            "meals": meals
        }

    except Exception as e:
        print("PREDICT MEALS ERROR:", e)
        return {
            "success": False,
            "message": "Failed to generate meals"
        }

class FinishOnboardingData(BaseModel):
    user_id: str
    name: str
    weight: float
    height: float
    dob: str
    goal: str
    dietaryPreference: str
    selectedRegularFoods: list
    allergies: str | None = None
    userNote: str | None = None

from datetime import datetime, date
from fastapi import HTTPException

def calculate_age(dob_str: str) -> int:
    dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age


@app.post("/api/finish-onboarding")
def finish_onboarding(data: FinishOnboardingData):
    try:
        user_id = data.user_id
        print(data.user_id, data.name, data.weight, data.height, data.dob, data.goal, data.dietaryPreference, data.selectedRegularFoods)
        # Calculate age from DOB
        age_value = calculate_age(data.dob)
        if data.allergies in ["None", "", None]:
            allergies_value = []
        else:
            allergies_value = [data.allergies]

        supabase_admin.table("profiles").update({
            "id": user_id,  # you can include this safely
            "name": data.name,
            "weight": data.weight,
            "height": data.height,
            "age": age_value,
            "diet_type": data.dietaryPreference,
            "allergies": allergies_value,
            "user_note": data.userNote,
            "created_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        # 2️⃣ INSERT / UPDATE regular foods
        supabase_admin.table("foods_regular").upsert({
            "user_id": user_id,
            "foods": data.selectedRegularFoods,
            "updated_at": datetime.utcnow().isoformat()
        }, on_conflict="user_id").execute()

        # 3️⃣ LOOKUP goal_id from goals table
        data_value = data.goal.title()
        goal_res = supabase_admin.table("goals") \
            .select("id, name") \
            .eq("name", data.goal.title()) \
            .maybe_single() \
            .execute()

        print("GOAL LOOKUP:", data.goal.title(), goal_res)
        if not goal_res.data:
            raise HTTPException(status_code=400, detail=f"Goal '{data.goal}' not found in database")
        goal_id = goal_res.data["id"]

        # 4️⃣ Deactivate previous goals
        supabase_admin.table("user_goals") \
            .update({"active": False}) \
            .eq("user_id", user_id) \
            .execute()

        # 5️⃣ Insert new active goal
        supabase_admin.table("user_goals").insert({
            "user_id": user_id,
            "goal_id": goal_id,
            "started_at": datetime.utcnow().isoformat(),
            "active": True
        }).execute()

        return {
            "success": True,
            "message": "Onboarding completed successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


FILE_PATH = "rtime.json"

def load_reflection_times():
    if not os.path.exists(FILE_PATH):
        return {}
    with open(FILE_PATH, "r") as f:
        return json.load(f)

def save_reflection_times(data):
    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=4)

def get_reflection_time(user_id):
    data = load_reflection_times()
    return data.get(user_id)

def set_reflection_time(user_id, time_str):
    data = load_reflection_times()
    data[user_id] = time_str
    save_reflection_times(data)

@app.post("/reflect-time")
def reflection_time(payload: dict):
    user_id = payload.get("user_id")
    if not user_id:
        return {"error": "user_id missing"}

    rt = get_reflection_time(user_id)
    print("REFLECTION TIME FOR", user_id, "is", rt)
    if rt:
        return {
            "hasReflectionTime": True,
            "reflectionTime": rt
        }
    else:
        return {
            "hasReflectionTime": False
        }

@app.post("/check-hs")
def check_health_score(payload: dict):
    user_id = payload.get("user_id")
    if not user_id:
        return {"error": "user_id missing"}

    # Query Supabase for health scores for this user
    res = supabase_admin.table("health_scores") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("date", desc=True) \
        .limit(1) \
        .execute()

    # If no rows found
    if not res.data:
        return {
            "hsExist": False
        }

    # Latest health score
    latest = res.data[0].get("score")

    return {
        "hsExist": True,
        "value": latest
    }


BASE_QUESTIONS = [
    {
        "id": "q_heaviness",
        "metric": "heaviness",
        "type": "rating",
        "question": "How heavy did your meals feel today?",
        "scale": {
            "min": 1,
            "max": 10,
            "labels": {
                "1": "Very light",
                "10": "Very heavy"
            }
        }
    },
    {
        "id": "q_energy",
        "metric": "energy",
        "type": "rating",
        "question": "How was your overall energy today?",
        "scale": {
            "min": 1,
            "max": 10,
            "labels": {
                "1": "Very low",
                "10": "Very high"
            }
        }
    },
    {
        "id": "q_balance",
        "metric": "balance",
        "type": "boolean",
        "question": "Did your meals feel balanced today?"
    },
    {
        "id": "q_digestion",
        "metric": "digestion",
        "type": "rating",
        "question": "How comfortable did you feel after eating?",
        "scale": {
            "min": 1,
            "max": 10,
            "labels": {
                "1": "Uncomfortable",
                "10": "Very comfortable"
            }
        }
    },
    {
        "id": "q_consistency",
        "metric": "consistency",
        "type": "boolean",
        "question": "Did you eat at roughly regular times today?"
    },
    {
        "id": "q_mindfulness",
        "metric": "mindfulness",
        "type": "rating",
        "question": "How aware were you while eating today?",
        "scale": {
            "min": 1,
            "max": 10,
            "labels": {
                "1": "Very distracted",
                "10": "Very present"
            }
        }
    }
]

from fastapi import Query

@app.get("/api/request-questions")
def get_reflection_questions(user_id: str = Query(...)):
    try:
        # Check if user has any health score entries
        result = (
            supabase_admin
            .table("health_scores")
            .select("id")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        has_history = len(result.data) > 0

        if has_history:
            # Placeholder for later agent-generated questions
            return {
                "type": "custom",
                "count": 0,
                "questions": [],
                "message": "Custom questions will be generated here"
            }

        # First-time user → base questions
        return {
            "type": "base",
            "count": len(BASE_QUESTIONS),
            "questions": BASE_QUESTIONS
        }

    except Exception as e:
        return {
            "type": "error",
            "message": str(e)
        }


# --- RECOMMEND FOODS ENDPOINT ---
import re

@app.post("/recommend-foods")
def recommend_foods(payload: dict):
    user_id = payload.get("user_id")
    if not user_id:
        return {"success": False, "message": "user_id missing"}

    try:
        # 1️⃣ Fetch regular foods for user
        foods_res = (
            supabase_admin
            .table("foods_regular")
            .select("foods")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        regular_foods = foods_res.data.get("foods", []) if foods_res.data else []

        # 2️⃣ Fetch user profile
        profile_res = (
            supabase_admin
            .table("profiles")
            .select("diet_type, allergies, user_note")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )

        if not profile_res.data:
            return {"success": False, "message": "Profile not found"}

        p = profile_res.data

        # 3️⃣ Gemini prompt
        prompt = f"""
You are a food recommendation engine for Indian diets.

Diet type: {p.get("diet_type")}
Allergies: {p.get("allergies")}
Notes: {p.get("user_note")}

Regular foods the user already eats (DO NOT repeat these):
{json.dumps(regular_foods)}

Recommend 5–8 additional foods the user might have eaten today.
Include home-cooked, outside food, and light snacks.
Return ONLY valid JSON in this exact format:

{{
  "recomfoods": ["food1", "food2", "food3"]
}}
"""

        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # 4️⃣ Clean Gemini output
        cleaned = (
            raw.replace("```json", "")
               .replace("```", "")
               .strip()
        )

        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        parsed = json.loads(match.group(0)) if match else {"recomfoods": []}

        return {
            "success": True,
            "regularfoods": regular_foods,
            "recomfoods": parsed.get("recomfoods", [])
        }

    except Exception as e:
        print("RECOMMEND FOODS ERROR:", e)
        return {
            "success": False,
            "message": str(e)
        }
