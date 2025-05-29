from flask import Flask, request, render_template
import numpy as np
import pandas as pd
import pickle
import random
from sklearn.preprocessing import LabelEncoder

# New imports for Gemini-based calorie chat & comparison
import re
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# Import API key from config file
from config import GOOGLE_API_KEY

# Set the API key for Google Gemini
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Load your datasets and model
data = pd.read_csv("Data Sets/Final Data set.csv")
Nutrient_recommend = pd.read_csv("Data Sets/Micro and macro nutrients.csv")
Meal_suggestions = pd.read_csv("Data Sets/Meal suggestions.csv")
RandomForest = pickle.load(open("model/RandomForest1.pkl", 'rb'))

app = Flask(__name__)

VALID_OPTIONS = {
    'Gender': {'Male': 0, 'Female': 1},
    'Diet_Preference': {
        'Non-Vegetarian': 0, 'Vegetarian': 1, 'Vegan': 2, 'Plant-Based': 3,
        'Mediterranean': 4, 'Keto': 5, 'Paleo': 6, 'Low-Carb': 7,
        'Gluten-Free': 8, 'Pescatarian': 9, 'Flexitarian': 10,
        'High-Protein': 11, 'DASH': 12, 'South Asian': 13, 'East Asian': 14,
        'Raw Vegan': 15, 'Halal': 16, 'Kosher': 17, 'Low-FODMAP': 18,
        'Mediterranean-Vegetarian': 19
    },
    'Activity_Level': {
        'Sedentary': 0, 'Light': 1, 'Moderate': 2, 'Active': 3, 'Very Active': 4
    },
    'Disease': {
        'None': 0, 'Diabetes': 1, 'Hypertension': 2, 'Heart Disease': 3,
        'GERD': 4, 'IBS': 5, 'Celiac': 6, 'Obesity': 7, 'Thyroid': 8,
        'Iron Deficiency': 9, 'B12 Deficiency': 10, 'Food Allergies': 11
    },
    'Food_Allergies': {
        'None': 0, 'Peanuts': 1, 'Tree Nuts': 2, 'Milk': 3, 'Eggs': 4,
        'Soy': 5, 'Fish': 6, 'Shellfish': 7, 'Wheat': 8, 'Multiple': 9
    },
    'Health_Goal': {
        'Weight Loss': 0, 'Maintenance': 1, 'Weight Gain': 2,
        'Muscle Gain': 3, 'Better Health': 4, 'Athletic Performance': 5
    }
}

MEAL_SUGGESTIONS = {
    'Vegetarian': {
        'breakfast': [
            'Oatmeal with protein powder, banana, nuts and seeds',
            'Greek yogurt parfait with granola, berries and honey',
            'Whole grain toast with avocado, scrambled eggs and spinach',
            'Protein smoothie bowl with mixed fruits, granola and chia seeds',
            'Cottage cheese pancakes with fresh fruits and maple syrup'
        ],
        'lunch': [
            'Quinoa bowl with roasted chickpeas, mixed vegetables and tahini dressing',
            'Lentil curry with brown rice and steamed vegetables',
            'Greek salad with feta cheese, olives and whole grain pita',
            'Vegetable stir-fry with tofu and brown rice',
            'Black bean and sweet potato burrito bowl with guacamole'
        ],
        'dinner': [
            'Tofu stir-fry with brown rice and mixed vegetables',
            'Chickpea curry with quinoa and roasted vegetables',
            'Black bean burgers with sweet potato wedges and salad',
            'Spinach and ricotta stuffed pasta with tomato sauce',
            'Buddha bowl with tempeh, roasted vegetables and tahini dressing'
        ],
        'snacks': [
            'Greek yogurt with honey and mixed nuts',
            'Protein smoothie with banana and peanut butter',
            'Trail mix with nuts, seeds and dried fruits',
            'Cottage cheese with fruit and granola',
            'Hummus with carrot sticks and whole grain crackers'
        ]
    },
    'Vegan': {
        'breakfast': [
            'Tofu scramble with vegetables and whole grain toast',
            'Overnight oats with plant milk, fruits and chia seeds',
            'Protein smoothie bowl with plant milk and granola',
            'Quinoa porridge with berries and almond butter',
            'Whole grain toast with avocado and tempeh bacon'
        ],
        'lunch': [
            'Buddha bowl with quinoa, tempeh and vegetables',
            'Lentil and vegetable curry with brown rice',
            'Chickpea salad sandwich with avocado',
            'Tofu and vegetable stir-fry with noodles',
            'Black bean and sweet potato tacos'
        ],
        'dinner': [
            'Tempeh stir-fry with brown rice and vegetables',
            'Lentil shepherd\'s pie with mushrooms',
            'Chickpea curry with quinoa',
            'Black bean burgers with sweet potato fries',
            'Pasta with vegetable and cashew cream sauce'
        ],
        'snacks': [
            'Mixed nuts and dried fruits',
            'Plant protein smoothie',
            'Hummus with vegetable sticks',
            'Energy balls made with dates and nuts',
            'Roasted chickpeas'
        ]
    }
}

def helper(calories):
    nutrient_info = Nutrient_recommend.iloc[
        (Nutrient_recommend['Daily_Calories'] - calories).abs().argsort()[:1]
    ].iloc[0]
    meal_info = Meal_suggestions.iloc[
        (Meal_suggestions['Daily_Calories'] - calories).abs().argsort()[:1]
    ].iloc[0]

    formatted_nutrients = {
        'Calories': f"<p><strong>Daily Calories:</strong> {nutrient_info['Daily_Calories']} kcal</p>",
        'Protein': f"<p><strong>Protein:</strong> {nutrient_info['Protein_g']} g</p>",
        'Carbs': f"<p><strong>Carbohydrates:</strong> {nutrient_info['Carbs_g']} g</p>",
        'Fat': f"<p><strong>Fat:</strong> {nutrient_info['Fat_g']} g</p>",
        'Fiber': f"<p><strong>Fiber:</strong> {nutrient_info['Fiber_g']} g</p>",
        'Sugar': f"<p><strong>Sugar:</strong> {nutrient_info['Sugar_g']} g</p>",
        'VitaminA': f"<p><strong>Vitamin A:</strong> {nutrient_info['Vitamin_A_mcg']} mcg</p>",
        'VitaminC': f"<p><strong>Vitamin C:</strong> {nutrient_info['Vitamin_C_mg']} mg</p>",
        'VitaminD': f"<p><strong>Vitamin D:</strong> {nutrient_info['Vitamin_D_mcg']} mcg</p>",
        'Calcium': f"<p><strong>Calcium:</strong> {nutrient_info['Calcium_mg']} mg</p>",
        'Iron': f"<p><strong>Iron:</strong> {nutrient_info['Iron_mg']} mg</p>",
        'Potassium': f"<p><strong>Potassium:</strong> {nutrient_info['Potassium_mg']} mg</p>",
        'Magnesium': f"<p><strong>Magnesium:</strong> {nutrient_info['Magnesium_mg']} mg</p>",
        'Zinc': f"<p><strong>Zinc:</strong> {nutrient_info['Zinc_mg']} mg</p>"
    }
    return formatted_nutrients, meal_info

def get_meal_suggestions(diet_pref, calories):
    diet_category = diet_pref if diet_pref in MEAL_SUGGESTIONS else 'Vegetarian'
    meals = MEAL_SUGGESTIONS[diet_category]
    formatted_meals = {
        'Breakfast': f"<p><strong>Breakfast:</strong> {random.choice(meals['breakfast'])}</p>",
        'Lunch': f"<p><strong>Lunch:</strong> {random.choice(meals['lunch'])}</p>",
        'Dinner': f"<p><strong>Dinner:</strong> {random.choice(meals['dinner'])}</p>",
        'Snacks': f"<p><strong>Snacks:</strong> {random.choice(meals['snacks'])}</p>"
    }
    return formatted_meals

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST', 'GET'])
def predict():
    if request.method == 'POST':
        try:
            age = request.form.get('Age')
            gender = request.form.get('Gender')
            weight = request.form.get('Weight')
            height = request.form.get('Height')
            diet_pref = request.form.get('Diet_Preference')
            activity = request.form.get('Activity_Level')
            weekly_activity = request.form.get('Weekly_Activity_Days')
            disease = request.form.get('Disease')
            allergies = request.form.get('Food_Allergies')
            goal = request.form.get('Health_Goal')

            user_data = {
                'Age': int(age),
                'Gender': gender,
                'Weight_kg': float(weight),
                'Height_cm': float(height),
                'Diet_Preference': diet_pref,
                'Activity_Level': activity,
                'Weekly_Activity_Days': int(weekly_activity),
                'Disease': disease,
                'Food_Allergies': allergies,
                'Health_Goal': goal
            }

            input_df = pd.DataFrame([user_data])
            for col in ['Gender','Diet_Preference','Activity_Level','Disease','Food_Allergies','Health_Goal']:
                input_df[col] = VALID_OPTIONS[col][input_df[col].iloc[0]]

            calories = int(RandomForest.predict(input_df)[0])
            nutrient_info, meal_info = helper(calories)
            meal_suggestions = get_meal_suggestions(diet_pref, calories)

            return render_template('index.html',
                                   calories=calories,
                                   nutrient_info=nutrient_info,
                                   meal_suggestions=meal_suggestions)
        except Exception as e:
            return f"An error occurred: {e}"
    return render_template('index.html')

# ─── Gemini Helpers & Chat Route ───────────────────────────────────────────

def run_calorie_estimator_once(food_list: str) -> float:
    template = """
Estimate the total calories for the following list of food items.
User Input: {foods}

Respond with only the numeric total calorie value, e.g., "345".
"""
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    prompt = ChatPromptTemplate.from_template(template)
    response = (prompt | model).invoke({"foods":food_list})
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", response.content)
    return float(m.group(1)) if m else 0.0

def run_adjustment_suggestion(expected: float, actual: float, food_list: str) -> str:
    template = """
You predicted a daily caloric goal of {expected} kcal, but the user's actual intake based on:
  {foods}
is {actual} kcal.

Please suggest how they can adjust quantities or add relevant dishes to hit their goal of {expected} kcal.
Respond in friendly, actionable bullet points.
"""
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    prompt = ChatPromptTemplate.from_template(template)
    return (prompt | model).invoke({
        "expected":str(expected),
        "actual":str(actual),
        "foods":food_list
    }).content.strip()

def run_general_conversation(user_message: str) -> str:
    """Handle general conversation with the user."""
    template = """
    You are a helpful nutrition and fitness assistant. The user is having a general conversation with you.
    Please respond in a friendly, helpful manner. If they ask about nutrition or fitness topics, provide
    accurate information. For other topics, be conversational but gently guide them back to health-related
    discussions when appropriate.
    
    User message: {message}
    
    Respond in a friendly, conversational tone.
    """
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    prompt = ChatPromptTemplate.from_template(template)
    return (prompt | model).invoke({"message":user_message}).content.strip()

def is_food_related(message: str) -> bool:
    """Determine if the message is related to food or calories."""
    food_keywords = ['food', 'eat', 'ate', 'eating', 'meal', 'breakfast', 'lunch', 'dinner', 
                    'snack', 'calorie', 'calories', 'diet', 'nutrition', 'hungry', 
                    'protein', 'carb', 'fat', 'vegetable', 'fruit', 'meat', 'dairy']
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in food_keywords)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form.get('message','').strip()
    expected_cal = request.form.get('expected_cal', type=float)

    if not user_message:
        chat_response = "Please enter a message or the foods you ate today."
    else:
        try:
            # Determine if the message is food-related or general conversation
            if is_food_related(user_message) and expected_cal > 0:
                # Handle food-related queries with calorie estimation
                actual_cal = run_calorie_estimator_once(user_message)
                suggestion = run_adjustment_suggestion(expected_cal, actual_cal, user_message)
                chat_response = (
                    f"Actual intake: {actual_cal:.1f} kcal\n\n"
                    f"Suggestions to reach {expected_cal:.1f} kcal:\n{suggestion}"
                )
            else:
                # Handle general conversation
                chat_response = run_general_conversation(user_message)
        except Exception as e:
            chat_response = f"Error: {e}"

    return render_template('index.html', chat_response=chat_response)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/developer')
def developer():
    return render_template('developer.html')

if __name__ == "__main__":
    app.run(debug=True)
