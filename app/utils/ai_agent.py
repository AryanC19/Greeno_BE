from ..service.crud_doctor_availabilty import get_doctor_by_specialty
from ..database import db

CAREPLANS_COLL = "careplans"

async def assign_slot_to_appointment(patient_id: str, appointment_id: str, specialty: str):
    # 1️⃣ Get doctor by specialty
    doctor = await get_doctor_by_specialty(specialty)
    if not doctor or "available_slots" not in doctor or not doctor["available_slots"]:
        return None
    available_slots = doctor["available_slots"]

    # 2️⃣ Get current booked slots for patient
    careplan = await db[CAREPLANS_COLL].find_one()
    booked_slots = [
        a.get("proposed_slot") for a in careplan.get("appointments", []) if a.get("proposed_slot")
    ]

    # 3️⃣ Find first free slot
    proposed_slot = None
    for slot in available_slots:
        if slot not in booked_slots:
            proposed_slot = slot
            break

    if not proposed_slot:
        return None

    # 4️⃣ Update appointment in careplan
    await db[CAREPLANS_COLL].update_one(
        {"patient_id": patient_id, "appointments.id": appointment_id},
        {"$set": {"appointments.$.proposed_slot": proposed_slot}}
    )

    return proposed_slot

from dotenv import load_dotenv
load_dotenv()
import os
import requests
import json
import re
from datetime import date
from typing import Dict, List, Optional
from fastapi import HTTPException

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "openai/gpt-4o-mini"
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def call_openrouter_api(prompt: str, system_prompt: Optional[str] = None) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENROUTER_MODEL,
        "messages": []
    }
    if system_prompt:
        data["messages"].append({"role": "system", "content": system_prompt})
    data["messages"].append({"role": "user", "content": prompt})
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise ValueError(f"OpenRouter API error: {response.text}")
    
def fetch_food_image(food_name: str) -> str:
    # Clean food name, removing parenthetical reason
    food_name = re.sub(r'\([^)]*\)', '', food_name).strip()
    if not food_name:
        return "https://images.pexels.com/photos/1/pexels-photo-1.jpeg"
    
    # Search for the exact food name first
    url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(food_name)}&per_page=10"
    headers = {"Authorization": f"{PEXELS_API_KEY}"}
    
    # Terms to exclude (people, non-food items)
    exclude_terms = [
        'person', 'people', 'man', 'woman', 'boy', 'girl', 'hand', 'hands', 'face', 'portrait', 
        'chef', 'waiter', 'child', 'kid', 'human', 'cooking', 'preparation', 'kitchen', 
        'cartoon', 'drawing', 'art', 'decoration', 'raw', 'garnish', 'unprepared'
    ]
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('photos'):
                for photo in data['photos']:
                    alt = photo.get('alt', '').lower()
                    # Only accept if food name is in alt text and no excluded terms
                    if (food_name.lower() in alt and 
                        not any(term in alt for term in exclude_terms) and
                        any(food_term in alt for food_term in ['food', 'dish', 'meal', 'fresh', 'healthy', 'eat', 'fruit', 'vegetable', 'grain', 'protein'])):
                        return photo['src']['medium']
                        
        # If no exact match, try with "food" added
        url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(food_name + ' food')}&per_page=5"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('photos'):
                for photo in data['photos']:
                    alt = photo.get('alt', '').lower()
                    if (food_name.lower() in alt and 
                        not any(term in alt for term in exclude_terms)):
                        return photo['src']['medium']
                        
    except Exception as e:
        print(f"Pexels API error for food: {food_name}: {e}")
    
    print(f"No suitable image found for food: {food_name}")
    return "https://images.pexels.com/photos/1/pexels-photo-1.jpeg"

def extract_descriptive_terms(description: str) -> str:
    system_prompt = """You are an assistant that extracts key descriptive terms for exercise video searches. Given an exercise description, return a single string with 1-3 concise terms (space-separated) that capture the specific focus of the exercise, excluding the exercise name, generic words like 'exercises', 'focusing', or durations (e.g., '30 minutes'). Example: For 'Gentle stretching exercises focusing on the legs and knees', return 'gentle leg knee'. Return only the terms, no JSON or extra text."""
    prompt = f"Description: {description}"
    try:
        terms = call_openrouter_api(prompt, system_prompt)
        return terms.strip()
    except Exception as e:
        print(f"OpenRouter terms extraction error: {e}")
        # Fallback to basic extraction
        words = description.lower().split()
        exclude = {'exercises', 'focusing', 'for', 'on', 'and', 'to', 'with', 'minutes', 'seconds'}
        terms = [word for word in words if word not in exclude and not word.isdigit()][:3]
        return ' '.join(terms) or 'exercise'
    
def fetch_exercise_video(exercise_name: str, description: str) -> str:
    descriptive_terms = extract_descriptive_terms(description)
    
    # Extract key terms from description for better matching
    description_words = description.lower().split()
    key_description_terms = [word for word in description_words if word in ['gentle', 'stretching', 'cardio', 'strength', 'flexibility', 'balance', 'low', 'high', 'intensity', 'beginner', 'advanced', 'rehabilitation', 'recovery', 'knee', 'back', 'shoulder', 'leg', 'arm', 'core', 'breathing']]
    
    # Try multiple search strategies, prioritizing exact matches with description context
    search_queries = [
        f"{exercise_name} {' '.join(key_description_terms)} exercise tutorial",
        f"{exercise_name} exercise tutorial how to",
        f"{exercise_name} {descriptive_terms} demonstration",
        f"how to do {exercise_name} {' '.join(key_description_terms)}",
        f"{exercise_name} exercise proper form",
        f"{exercise_name} {descriptive_terms} tutorial",
        f"{exercise_name} exercise video"
    ]
    
    try:
        for query in search_queries:
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={requests.utils.quote(query)}&key={YOUTUBE_API_KEY}&type=video&videoCategoryId=17&maxResults=15"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    for item in data['items']:
                        title = item['snippet']['title'].lower()
                        desc = item['snippet']['description'].lower()
                        
                        # Skip irrelevant content
                        if any(term in title + desc for term in ['cartoon', 'anime', 'meme', 'game', 'animation', 'music', 'song', 'comedy', 'funny']):
                            continue
                        
                        # Prioritize videos that mention the specific exercise name AND description context
                        if exercise_name.lower() in title:
                            # Check if description context matches (gentle, stretching, etc.)
                            context_match = any(term in title + desc for term in key_description_terms)
                            exercise_related = any(term in title + desc for term in ['exercise', 'workout', 'fitness', 'training', 'tutorial', 'how to', 'demonstration', 'form'])
                            
                            if exercise_related and (context_match or not key_description_terms):
                                video_id = item['id']['videoId']
                                return f"https://www.youtube.com/watch?v={video_id}"
                        
                        # Secondary option: exercise-related with descriptive terms from description
                        elif (any(term in title for term in descriptive_terms.split() if term) and 
                              any(term in title + desc for term in ['exercise', 'workout', 'fitness', 'training', 'tutorial']) and
                              any(term in title + desc for term in key_description_terms if key_description_terms)):
                            video_id = item['id']['videoId']
                            return f"https://www.youtube.com/watch?v={video_id}"
        
        # If no good match found, return None
        return None
    except Exception as e:
        print(f"YouTube API error: {e}")
        return None

def parse_sections(text: str) -> Dict[str, str]:
    sections = {'history': '', 'concern': '', 'current_diet': '', 'lab_reports': '', 'allergies': ''}
    patterns = [
        ('history', r'(?:Medical |Patient )History:?\s*(.*?)(?=\n[A-Z][a-z]+:|\Z)'),
        ('concern', r'(?:Patient |Chief )Concern[s]?:?\s*(.*?)(?=\n[A-Z][a-z]+:|\Z)'),
        ('current_diet', r'(?:Current |Patient )Diet:?\s*(.*?)(?=\n[A-Z][a-z]+:|\Z)'),
        ('lab_reports', r'(?:Lab |Laboratory |Test )Report[s]?:?\s*(.*?)(?=\n[A-Z][a-z]+:|\Z)'),
        ('allergies', r'(?:Allergies|Food Allergies):?\s*(.*?)(?=\n[A-Z][a-z]+:|\Z)')
    ]
    for key, pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        sections[key] = match.group(1).strip() if match else ''
    return sections

def extract_entities(text: str, lab_reports: str, allergies: str) -> Dict:
    system_prompt = """You are a medical AI assistant. Extract information from the provided medical text, lab reports (if any), and allergies (if any) and return a valid JSON object only, no extra text or code blocks, that can be parsed by json.loads, with:
- 'conditions': List of conditions/diseases from history, concern, or lab reports (e.g., 'low iron' from lab reports).
- 'concern': Main patient concern or symptom (e.g., 'high blood sugar').
- 'lab_metrics': List of key lab results (e.g., ['low hemoglobin', 'high cholesterol']) or empty list if none.
- 'allergies': List of food allergies (e.g., ['peanuts', 'shellfish']) or empty list if none.
- Today is {today}.
Return valid JSON only, nothing else."""
    prompt = f"Medical text: {text}\nLab reports: {lab_reports or 'None'}\nAllergies: {allergies or 'None'}"
    response = call_openrouter_api(prompt, system_prompt.format(today=date.today().strftime('%Y-%m-%d')))
    try:
        data = json.loads(response)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e} - Response: {response}")
        data = {}
    return data or {
        'conditions': [], 'concern': '', 'lab_metrics': [], 'allergies': []
    }

def analyze_current_diet(current_diet: str, conditions: List[str], concern: str, lab_metrics: List[str], allergies: List[str]) -> str:
    if not current_diet.strip():
        return ""
    
    # Clean parenthetical notes (e.g., "dessert (gulab jamun)" -> "gulab jamun")
    current_diet = re.sub(r'\([^)]*\)', lambda m: m.group(0).strip('()'), current_diet)
    
    # Parse foods, splitting on meal labels, conjunctions, commas, semicolons, periods
    foods = [food.strip() for food in re.split(r'[,\s;]+and\s*|[,\s;]+|[:\n]+|with\s+|[.]', current_diet) 
             if food.strip() and not food.lower() in ['breakfast', 'lunch', 'dinner', 'snacks', 'evening', 'morning', 'dessert']]
    foods = list(dict.fromkeys(foods))  # Remove duplicates
    if not foods:
        return "In your current diet, no specific foods were identified. Adopting healthier options can enhance your well-being."
    
    system_prompt = """You are a medical AI assistant. Given the patient's current diet (list of foods), medical conditions, concern, lab metrics (if any), and allergies (if any), analyze each food to determine its healthiness based on its nutritional content (e.g., fiber, sugar, fat) and suitability for the patient's conditions, concern, and lab metrics. Exclude any foods listed as allergies from being considered healthy. Return a valid JSON object only, no extra text or code blocks, that can be parsed by json.loads, with:
- 'healthy_foods': List of foods beneficial for the patient's health (e.g., ['steamed broccoli']). Consider high fiber, low sugar, low saturated fat, etc.
- 'unhealthy_foods': List of foods that are not optimal or should be avoided, including allergens (e.g., ['gulab jamun']). Identify high sugar, high saturated fat, etc.
- 'analysis': List of objects, one per food, with:
  - 'food': The food name (e.g., 'gulab jamun').
  - 'healthy': Boolean indicating if the food is beneficial (true) or not (false).
  - 'reason': Brief explanation of why the food is healthy or unhealthy (e.g., 'High in sugar, may spike blood sugar').
Ensure every food is analyzed, even if vague or a complex dish (e.g., 'paneer butter masala'). Treat dishes like 'gulab jamun' (high-sugar dessert) or 'samosa' (fried) as generally unhealthy unless specific conditions suggest otherwise. If no foods are healthy or all are allergens, healthy_foods can be empty. If no foods are unhealthy, unhealthy_foods can be empty. Return valid JSON only."""
    prompt = f"Current diet: {', '.join(foods)}\nConditions: {', '.join(conditions) or 'None'}\nConcern: {concern or 'None'}\nLab metrics: {', '.join(lab_metrics) or 'None'}\nAllergies: {', '.join(allergies) or 'None'}"
    try:
        response = call_openrouter_api(prompt, system_prompt)
        result = json.loads(response)
        healthy_foods = result.get('healthy_foods', [])
        unhealthy_foods = result.get('unhealthy_foods', [])
        analysis = result.get('analysis', [])
        
        # Validate analysis covers all foods
        analyzed_foods = {item['food'].lower() for item in analysis}
        if not all(food.lower() in analyzed_foods for food in foods):
            print(f"Warning: Not all foods analyzed. Foods: {foods}, Analyzed: {analyzed_foods}")
            missing_foods = [food for food in foods if food.lower() not in analyzed_foods]
            unhealthy_foods.extend(missing_foods)
            analysis.extend([{'food': food, 'healthy': False, 'reason': 'Not analyzed, assumed suboptimal'} for food in missing_foods])
        
        # Format output
        if healthy_foods:
            return f"In your current diet, the following foods are healthy and beneficial: {', '.join(healthy_foods)}. These choices support your health goals. The remaining foods are not optimal; consider replacing them with healthier options to enhance your well-being."
        else:
            return f"In your current diet, no foods were identified as healthy and beneficial. The listed foods are not optimal; consider replacing them with healthier options to enhance your well-being."
    except (json.JSONDecodeError, Exception) as e:
        print(f"Current diet analysis error: {e} - Response: {response if 'response' in locals() else 'No response'}")
        return f"In your current diet, no foods were identified as healthy and beneficial. The listed foods ({', '.join(foods)}) are not optimal; consider replacing them with healthier options to enhance your well-being."

def generate_suggestions(conditions: List[str], concern: str, current_diet: str, lab_metrics: List[str], allergies: List[str]) -> Dict:
    conditions_str = ', '.join(conditions) or 'None'
    concern_str = concern or 'None'
    lab_metrics_str = ', '.join(lab_metrics) or 'None'
    allergies_str = ', '.join(allergies) or 'None'
    prompt = f"""Patient conditions: {conditions_str}. Concern: {concern_str}. Lab metrics: {lab_metrics_str}. Allergies: {allergies_str}.
Provide valid JSON object only, no extra text or code blocks, that can be parsed by json.loads, with:
    - 'diet_plan': List of exactly 5-7 objects, each with:
        - 'nutrient': A specific nutrient needed based on the patient's conditions, concern, and lab metrics (e.g., 'Fiber', 'Iron').
        - 'food': A SIMPLE, COMMON, cooked or ready-to-eat dish (not just a raw ingredient) that is rich in that nutrient (e.g., 'Vegetable Soup', 'Egg Curry', 'Rice Porridge', 'Carrot Halwa'). DO NOT use complicated, fortified, or branded foods. The food name must be a general, recognizable dish that is easy to find and suitable for a clear image (no people, no packaging, just the dish itself).
        - 'reason': A brief explanation of why the dish helps the patient's condition, concern, or lab metrics (e.g., 'Helps regulate blood sugar').
        Suggestions must be personalized, focusing on nutrients that support health improvement and avoiding allergens. The dish must be suitable for finding a clear image of the food only (no people, no packaging, just the dish itself).
    - 'exercise_plan': List of exactly 5-7 objects, each with:
        - 'name': A concise exercise name (e.g., 'Walking', 'Stretching', 'Swimming') suitable for searching videos.
        - 'description': A short description of the exercise tailored to the patient's conditions, concern, and lab metrics (e.g., 'Gentle stretching exercises focusing on the legs and knees').
        Exercises must be personalized to help the patient recover and improve health (e.g., gentle exercises for low hemoglobin, cardio for high cholesterol).
    All suggestions must be personalized, not generic, and diet suggestions must exclude allergens. Return valid JSON only."""
    try:
        response = call_openrouter_api(prompt)
        suggestions = json.loads(response)
        # Add diet analysis and image URLs to diet_plan
        diet_with_images = []
        if current_diet:
            diet_analysis = analyze_current_diet(current_diet, conditions, concern, lab_metrics, allergies)
            if diet_analysis:
                diet_with_images.append({"analysis": diet_analysis})
        else:
            diet_with_images.append({"analysis": "To support your recovery and improve your health, include these nutrient-rich foods tailored to your needs."})
        # For each suggested food, pair with its image and nutrition
        for sugg in suggestions.get('diet_plan', []):
            nutrient = sugg.get('nutrient', '')
            food = sugg.get('food', '')
            dish = sugg.get('dish', '')
            reason = sugg.get('reason', '')
            if not nutrient or not food or not reason:
                continue
            if any(allergen.lower() in food.lower() for allergen in allergies):
                continue
            image_url = fetch_food_image(food)
            # If no image found (default placeholder), try alternative foods for the same nutrient
            if image_url.endswith('/1/pexels-photo-1.jpeg'):
                # Try up to 3 alternative foods for the same nutrient using the AI
                alt_prompt = f"List 3 simple, common, cooked or ready-to-eat foods (not raw ingredients) rich in {nutrient}, excluding {food}. Only list the food names, comma separated."
                try:
                    alt_foods_str = call_openrouter_api(alt_prompt)
                    alt_foods = [f.strip() for f in alt_foods_str.split(',') if f.strip()]
                    found = False
                    for alt_food in alt_foods:
                        if any(allergen.lower() in alt_food.lower() for allergen in allergies):
                            continue
                        alt_image_url = fetch_food_image(alt_food)
                        if not alt_image_url.endswith('/1/pexels-photo-1.jpeg'):
                            # Found a real image
                            diet_with_images.append({
                                "nutrient": nutrient,
                                "food": alt_food,
                                "dish": dish,
                                "reason": reason,
                                "image_url": alt_image_url
                            })
                            found = True
                            break
                    if not found:
                        continue  # Skip if no image found for any food
                except Exception as e:
                    print(f"Error finding alternative food for {nutrient}: {e}")
                    continue
            else:
                diet_with_images.append({
                    "nutrient": nutrient,
                    "food": food,
                    "dish": dish,
                    "reason": reason,
                    "image_url": image_url
                })
        suggestions['diet_plan'] = diet_with_images
        
        # Add video URLs to exercise_plan in structured format
        exercise_with_videos = []
        for ex in suggestions.get('exercise_plan', []):
            name = ex.get('name', '')
            description = ex.get('description', '')
            if not name or not description:
                continue
            video_url = fetch_exercise_video(name, description)
            if video_url:
                exercise_with_videos.append({
                    "name": name,
                    "reason": description,
                    "video_url": video_url
                })
            else:
                # Include exercise without video if no video found
                exercise_with_videos.append({
                    "name": name,
                    "reason": description,
                    "video_url": "No video available"
                })
        suggestions['exercise_plan'] = exercise_with_videos
        
        return suggestions
    except (json.JSONDecodeError, Exception) as e:
        print(f"Suggestions error: {e} - Response: {response if 'response' in locals() else 'No response'}")
        return {
            'diet_plan': ["To support your recovery and improve your health, include these nutrient-rich foods tailored to your needs.", "Try to include the following foods to improve your diet"],
            'exercise_plan': []
        }

def get_medicine_reason(medicine_name: str) -> str:
    """
    Calls OpenRouter API to fetch ONLY the reason for prescription in JSON format.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a medical assistant. "
                    "Return ONLY valid JSON in the form {\"reason\": \"...\"}. "
                    "The reason should be 1–2 sentences explaining why the medicine is prescribed. "
                    "Do NOT include dosage, side effects, or instructions. JSON only, no extra text."
                )
            },
            {
                "role": "user",
                "content": f"Explain why {medicine_name} is prescribed."
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="❌ Error fetching medicine info.")

    result = response.json()
    raw_output = result["choices"][0]["message"]["content"].strip()

    try:
        parsed = json.loads(raw_output)
        return parsed.get("reason", "No reason found")
    except Exception:
        return raw_output  # fallback if parsing fails
