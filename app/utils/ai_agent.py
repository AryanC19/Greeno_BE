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
    
    # Handle food name variations for edible, prominent dishes
    food_dish_variations = {
        'kiwifruit': ['kiwi salad', 'kiwi smoothie', 'kiwi tart'],
        'greek yogurt': ['yogurt parfait', 'greek yogurt bowl', 'yogurt smoothie'],
        'chia seeds': ['chia seed pudding', 'chia smoothie', 'chia bowl'],
        'quinoa': ['quinoa salad', 'quinoa bowl', 'quinoa stir-fry'],
        'salmon': ['grilled salmon', 'salmon fillet', 'salmon salad'],
        'lentils': ['lentil soup', 'lentil curry', 'lentil salad'],
        'spinach': ['spinach salad', 'sautéed spinach', 'spinach curry'],
        'almonds': ['almond butter toast', 'almond salad', 'roasted almonds'],
        'avocado': ['avocado toast', 'avocado salad', 'guacamole'],
        'broccoli': ['broccoli stir-fry', 'sautéed broccoli', 'broccoli salad'],
        'oatmeal': ['oatmeal bowl', 'oat porridge', 'oat pancakes'],
        'banana': ['banana smoothie', 'banana bread', 'banana pancakes'],
        'white rice': ['white rice bowl', 'white rice stir-fry'],
        'chicken curry': ['chicken curry', 'chicken tikka masala'],
        'mashed potatoes': ['mashed potatoes', 'potato casserole'],
        'roti': ['roti with curry', 'roti wrap', 'indian flatbread'],
        'paneer butter masala': ['paneer butter masala', 'paneer curry'],
        'gulab jamun': ['gulab jamun', 'indian dessert'],
        'samosa': ['samosa', 'fried samosa'],
        'tea': ['herbal tea', 'chai tea'],
        'chips': ['potato chips', 'baked chips'],
        'soft drinks': ['soda drink', 'carbonated beverage'],
        'chicken': ['grilled chicken', 'chicken salad', 'chicken curry'],
        'tofu': ['tofu stir-fry', 'tofu scramble', 'tofu curry'],
        'brown rice': ['brown rice bowl', 'brown rice stir-fry'],
        'kale': ['kale salad', 'sautéed kale', 'kale smoothie'],
    }
    
    # Prioritize dish-specific queries, limit to 3 queries for efficiency
    queries = []
    if food_name.lower() in food_dish_variations:
        queries.extend(food_dish_variations[food_name.lower()][:2])  # Top 2 dish variations
    queries.append(f"{food_name} dish")  # Generic dish query
    if len(queries) < 3:
        queries.append(f"{food_name} food")  # Fallback to food query
    
    best_image = None
    best_score = -1
    for query in queries[:3]:  # Limit to 3 queries to optimize Pexels API usage
        url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(query)}&per_page=5"
        headers = {"Authorization": f"{PEXELS_API_KEY}"}
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get('photos'):
                    for photo in data['photos']:
                        alt = photo.get('alt', '').lower()
                        src = photo.get('src', {}).get('original', '').lower()
                        # Exclude non-food or non-edible images
                        if any(term in alt + src for term in ['cartoon', 'drawing', 'art', 'decoration', 'raw', 'garnish', 'unprepared']):
                            continue
                        # Score image relevance, prioritizing edible dishes where food is prominent
                        score = 0
                        if any(term in alt + src for term in ['cooked', 'sauté', 'stir-fry', 'roasted', 'grilled', 'curry', 'salad', 'dish', 'soup', 'pudding', 'toast', 'smoothie', 'bowl', 'dessert', 'flatbread']):
                            score += 4  # Higher weight for prepared dishes
                        if food_name.lower() in alt + src:
                            score += 3  # Ensure food is mentioned
                        if any(var in alt + src for var in food_dish_variations.get(food_name.lower(), [])):
                            score += 2  # Prefer specific dish variations
                        if any(term in alt + src for term in ['food', 'edible', 'meal']):
                            score += 1  # General food relevance
                        if any(term in alt + src for term in ['raw', 'ingredient', 'garnish']):
                            score -= 2  # Penalize non-edible or non-prominent images
                        if score > best_score:
                            best_score = score
                            best_image = photo['src']['medium']
                    if best_image:
                        return best_image
        except Exception as e:
            print(f"Pexels API error for query '{query}' (food: {food_name}): {e}")
    
    # Fallback to single generic query
    url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(food_name + ' dish')}&per_page=1"
    headers = {"Authorization": f"{PEXELS_API_KEY}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('photos'):
                return data['photos'][0]['src']['medium']
    except Exception as e:
        print(f"Pexels API fallback error for food: {food_name}: {e}")
    
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
    query = f"{exercise_name} {descriptive_terms} exercise human demonstration"
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={requests.utils.quote(query)}&key={YOUTUBE_API_KEY}&type=video&videoCategoryId=17&maxResults=5"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                for item in data['items']:
                    title = item['snippet']['title'].lower()
                    description = item['snippet']['description'].lower()
                    # Discard if cartoon, anime, or meme
                    if any(term in title + description for term in ['cartoon', 'anime', 'meme']):
                        continue
                    # Prioritize if matches exercise name and descriptive terms
                    if exercise_name.lower() in title + description and \
                       any(term in title + description for term in descriptive_terms.split()):
                        video_id = item['id']['videoId']
                        # Prefer Shorts if available
                        if 'shorts' in item['snippet']['thumbnails']['default']['url']:
                            return f"https://www.youtube.com/shorts/{video_id}"
                        return f"https://www.youtube.com/watch?v={video_id}"
                # Fallback to first video
                video_id = data['items'][0]['id']['videoId']
                return f"https://www.youtube.com/watch?v={video_id}"
        return "https://www.youtube.com/watch?v=placeholder"  # Placeholder if no video found
    except Exception as e:
        print(f"YouTube API error: {e}")
        return "https://www.youtube.com/watch?v=placeholder"

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
- 'nutrition_plan': List of 5-10 objects, each with:
  - 'nutrient': A specific nutrient needed based on the patient's conditions, concern, and lab metrics (e.g., 'Fiber', 'Iron').
  - 'food': A food rich in that nutrient, tailored to aid recovery (e.g., 'Lentils', 'Spinach'). Do NOT include any foods listed in allergies.
  - 'reason': A brief explanation of why the nutrient/food helps the patient's condition, concern, or lab metrics (e.g., 'Helps regulate blood sugar').
  Suggestions must be personalized, focusing on nutrients that support health improvement and avoiding allergens.
- 'exercise_plan': List of 3-5 objects, each with:
  - 'name': A concise exercise name (e.g., 'Stretching', 'Swimming') suitable for searching videos.
  - 'description': A short description of the exercise tailored to the patient's conditions, concern, and lab metrics (e.g., 'Gentle stretching exercises focusing on the legs and knees').
  Exercises must be personalized to help the patient recover and improve health (e.g., gentle exercises for low hemoglobin, cardio for high cholesterol).
All suggestions must be personalized, not generic, and nutrition suggestions must exclude allergens. Return valid JSON only."""
    try:
        response = call_openrouter_api(prompt)
        suggestions = json.loads(response)
        # Add diet analysis and image URLs to nutrition_plan
        nutrition_with_images = []
        if current_diet:
            diet_analysis = analyze_current_diet(current_diet, conditions, concern, lab_metrics, allergies)
            if diet_analysis:
                nutrition_with_images.append(diet_analysis)
        else:
            nutrition_with_images.append("To support your recovery and improve your health, include these nutrient-rich foods tailored to your needs.")
        nutrition_with_images.append("Try to include the following foods to improve your nutrition")
        for sugg in suggestions.get('nutrition_plan', []):
            nutrient = sugg.get('nutrient', '')
            food = sugg.get('food', '')
            reason = sugg.get('reason', '')
            if not nutrient or not food or not reason:
                continue
            # Double-check that suggested food is not an allergen
            if any(allergen.lower() in food.lower() for allergen in allergies):
                continue
            image_url = fetch_food_image(food)
            nutrition_with_images.append(f"{nutrient}: {food} ({reason})\n{image_url}")
        suggestions['nutrition_plan'] = nutrition_with_images
        
        # Add video URLs to exercise_plan
        exercise_with_videos = []
        for ex in suggestions.get('exercise_plan', []):
            name = ex.get('name', '')
            description = ex.get('description', '')
            if not name or not description:
                continue
            video_url = fetch_exercise_video(name, description)
            exercise_with_videos.append(f"{name}: {description}\n{video_url}")
        suggestions['exercise_plan'] = exercise_with_videos
        
        return suggestions
    except (json.JSONDecodeError, Exception) as e:
        print(f"Suggestions error: {e} - Response: {response if 'response' in locals() else 'No response'}")
        return {
            'nutrition_plan': ["To support your recovery and improve your health, include these nutrient-rich foods tailored to your needs.", "Try to include the following foods to improve your nutrition"],
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
