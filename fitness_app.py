import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from pathlib import Path

# Page configuration
st.set_page_config(page_title="Fitness & Nutrition Tracker", page_icon="💪", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF4B4B;
        text-align: center;
        padding: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1F77B4;
        margin-top: 2rem;
    }
    .meal-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #FF4B4B;
    }
    .workout-card {
        background-color: #e8f4f8;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #1F77B4;
    }
    .metric-card {
        background-color: #fff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .notification-box {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'start_date' not in st.session_state:
    st.session_state.start_date = datetime.now()
if 'current_weight' not in st.session_state:
    st.session_state.current_weight = 74.5
if 'weight_log' not in st.session_state:
    st.session_state.weight_log = {datetime.now().strftime('%Y-%m-%d'): 74.5}
if 'workout_completed' not in st.session_state:
    st.session_state.workout_completed = {}
if 'meals_completed' not in st.session_state:
    st.session_state.meals_completed = {}

# Your personalized data
CURRENT_WEIGHT = 74.5
TARGET_WEIGHT = 70.0
GOAL_PERIOD = 90  # 3 months
WEEKLY_LOSS = (CURRENT_WEIGHT - TARGET_WEIGHT) / (GOAL_PERIOD / 7)  # ~0.38 kg per week

# Calculate daily caloric needs
# For 74.5 kg, moderate activity, male (assumed): BMR ≈ 1800
# For muscle gain + fat loss: deficit of 300-500 calories
DAILY_CALORIES = 2200
PROTEIN_G = 150  # 2g per kg body weight
CARBS_G = 220
FATS_G = 60

# Comprehensive 3-Month Workout Plan
WORKOUT_PLAN = {
    "Monday": {
        "focus": "Chest & Triceps",
        "exercises": [
            {"name": "Bench Press", "sets": 4, "reps": "8-10", "rest": "90s"},
            {"name": "Incline Dumbbell Press", "sets": 3, "reps": "10-12", "rest": "60s"},
            {"name": "Cable Chest Fly", "sets": 3, "reps": "12-15", "rest": "60s"},
            {"name": "Push-ups", "sets": 3, "reps": "15-20", "rest": "45s"},
            {"name": "Tricep Dips", "sets": 3, "reps": "10-12", "rest": "60s"},
            {"name": "Tricep Pushdowns", "sets": 3, "reps": "12-15", "rest": "45s"},
            {"name": "Overhead Tricep Extension", "sets": 3, "reps": "12-15", "rest": "45s"},
        ],
        "cardio": "10 min treadmill warm-up, 15 min HIIT post-workout"
    },
    "Tuesday": {
        "focus": "Back & Biceps",
        "exercises": [
            {"name": "Pull-ups/Lat Pulldown", "sets": 4, "reps": "8-10", "rest": "90s"},
            {"name": "Barbell Rows", "sets": 4, "reps": "8-10", "rest": "90s"},
            {"name": "Seated Cable Rows", "sets": 3, "reps": "10-12", "rest": "60s"},
            {"name": "Face Pulls", "sets": 3, "reps": "15-20", "rest": "45s"},
            {"name": "Dumbbell Bicep Curls", "sets": 4, "reps": "10-12", "rest": "60s"},
            {"name": "Hammer Curls", "sets": 3, "reps": "12-15", "rest": "45s"},
            {"name": "Cable Bicep Curls", "sets": 3, "reps": "12-15", "rest": "45s"},
        ],
        "cardio": "10 min cycling warm-up, 20 min steady-state cardio"
    },
    "Wednesday": {
        "focus": "Legs & Core",
        "exercises": [
            {"name": "Squats", "sets": 4, "reps": "8-10", "rest": "2min"},
            {"name": "Leg Press", "sets": 3, "reps": "10-12", "rest": "90s"},
            {"name": "Romanian Deadlifts", "sets": 3, "reps": "10-12", "rest": "90s"},
            {"name": "Leg Curls", "sets": 3, "reps": "12-15", "rest": "60s"},
            {"name": "Calf Raises", "sets": 4, "reps": "15-20", "rest": "45s"},
            {"name": "Planks", "sets": 3, "reps": "60s hold", "rest": "60s"},
            {"name": "Hanging Leg Raises", "sets": 3, "reps": "12-15", "rest": "60s"},
        ],
        "cardio": "15 min stair climber"
    },
    "Thursday": {
        "focus": "Shoulders & Arms",
        "exercises": [
            {"name": "Overhead Press", "sets": 4, "reps": "8-10", "rest": "90s"},
            {"name": "Lateral Raises", "sets": 4, "reps": "12-15", "rest": "60s"},
            {"name": "Front Raises", "sets": 3, "reps": "12-15", "rest": "60s"},
            {"name": "Rear Delt Fly", "sets": 3, "reps": "12-15", "rest": "60s"},
            {"name": "Barbell Curls", "sets": 3, "reps": "10-12", "rest": "60s"},
            {"name": "Skull Crushers", "sets": 3, "reps": "10-12", "rest": "60s"},
            {"name": "21s (Biceps)", "sets": 2, "reps": "21", "rest": "90s"},
        ],
        "cardio": "20 min cycling intervals"
    },
    "Friday": {
        "focus": "Full Body Power",
        "exercises": [
            {"name": "Deadlifts", "sets": 4, "reps": "6-8", "rest": "2min"},
            {"name": "Incline Bench Press", "sets": 3, "reps": "8-10", "rest": "90s"},
            {"name": "Weighted Pull-ups", "sets": 3, "reps": "6-8", "rest": "90s"},
            {"name": "Dumbbell Shoulder Press", "sets": 3, "reps": "10-12", "rest": "60s"},
            {"name": "Cable Rows", "sets": 3, "reps": "10-12", "rest": "60s"},
            {"name": "Dips", "sets": 3, "reps": "10-12", "rest": "60s"},
        ],
        "cardio": "15 min HIIT treadmill sprints"
    },
    "Saturday": {
        "focus": "Active Recovery & Core",
        "exercises": [
            {"name": "Light Cardio (Walking/Cycling)", "sets": 1, "reps": "30-45 min", "rest": "-"},
            {"name": "Yoga/Stretching", "sets": 1, "reps": "20 min", "rest": "-"},
            {"name": "Planks", "sets": 3, "reps": "60s", "rest": "60s"},
            {"name": "Russian Twists", "sets": 3, "reps": "20", "rest": "45s"},
            {"name": "Mountain Climbers", "sets": 3, "reps": "30s", "rest": "45s"},
        ],
        "cardio": "Light activity only"
    },
    "Sunday": {
        "focus": "Rest Day",
        "exercises": [
            {"name": "Complete Rest or Light Walk", "sets": 1, "reps": "30 min", "rest": "-"},
            {"name": "Meal Prep for Week", "sets": 1, "reps": "-", "rest": "-"},
            {"name": "Recovery & Sleep Focus", "sets": 1, "reps": "8+ hours", "rest": "-"},
        ],
        "cardio": "Optional: 20 min walk"
    }
}

# Comprehensive Meal Plan
MEAL_PLAN = {
    "Early Morning (6:00 AM)": {
        "items": [
            "1 glass warm water with lemon",
            "5-10 soaked almonds",
        ],
        "calories": 80,
        "protein": 3,
        "purpose": "Kickstart metabolism"
    },
    "Pre-Workout (7:00 AM)": {
        "items": [
            "1 banana",
            "1 scoop whey protein with water",
            "Black coffee (optional)",
        ],
        "calories": 200,
        "protein": 25,
        "purpose": "Energy for workout"
    },
    "Breakfast (9:00 AM)": {
        "items": [
            "4 egg whites + 1 whole egg (scrambled/boiled)",
            "2 whole wheat bread slices or 1 cup oats",
            "1 cup milk or greek yogurt",
            "Mixed vegetables (cucumber, tomato)",
        ],
        "calories": 450,
        "protein": 35,
        "purpose": "Post-workout recovery"
    },
    "Mid-Morning Snack (11:30 AM)": {
        "items": [
            "1 apple or orange",
            "10-12 roasted cashews or peanuts",
            "Green tea",
        ],
        "calories": 180,
        "protein": 5,
        "purpose": "Sustained energy"
    },
    "Lunch (1:30 PM)": {
        "items": [
            "150g grilled chicken breast or 200g paneer/tofu",
            "1.5 cups brown rice or 3 chapatis",
            "1 cup dal (lentils)",
            "Large mixed salad with olive oil",
            "1 cup curd/yogurt",
        ],
        "calories": 600,
        "protein": 45,
        "purpose": "Main meal - muscle building"
    },
    "Evening Snack (4:30 PM)": {
        "items": [
            "1 cup sprouts or boiled chickpeas",
            "Green tea or buttermilk",
            "4-5 whole grain crackers",
        ],
        "calories": 200,
        "protein": 12,
        "purpose": "Pre-evening energy"
    },
    "Dinner (8:00 PM)": {
        "items": [
            "150g grilled fish/chicken or 150g paneer",
            "2 chapatis or 1 cup quinoa",
            "Mixed vegetable curry (no oil)",
            "Clear vegetable soup",
            "Small bowl of salad",
        ],
        "calories": 450,
        "protein": 40,
        "purpose": "Light dinner for recovery"
    },
    "Before Bed (10:00 PM)": {
        "items": [
            "1 glass warm milk or casein protein shake",
            "5 almonds",
        ],
        "calories": 150,
        "protein": 10,
        "purpose": "Overnight muscle recovery"
    }
}

# Notification schedule
NOTIFICATIONS = {
    "06:00": "⏰ Good Morning! Time to wake up and drink warm lemon water",
    "07:00": "🍌 Pre-workout meal time! Have banana + protein shake",
    "07:30": "💪 GYM TIME! Let's crush today's workout",
    "09:00": "🍳 Post-workout breakfast - Your muscles need protein!",
    "11:30": "🍎 Mid-morning snack time - Stay fueled",
    "13:30": "🍽️ Lunch time - Your biggest meal of the day",
    "16:30": "☕ Evening snack - Healthy options only",
    "20:00": "🌙 Dinner time - Keep it light and protein-rich",
    "22:00": "🥛 Before bed - Warm milk for recovery",
    "22:30": "😴 Sleep time - Recovery is crucial for muscle growth"
}

# Tips and guidelines
NUTRITION_TIPS = [
    "Drink 3-4 liters of water daily",
    "Avoid sugar, fried foods, and processed snacks",
    "Eat protein with every meal (eggs, chicken, fish, paneer, dal)",
    "Include green vegetables in lunch and dinner",
    "No eating after 10 PM",
    "Cheat meal allowed once per week (Sunday lunch)",
    "Track your weight every Monday morning",
    "Sleep 7-8 hours daily for muscle recovery",
    "Take rest days seriously - muscles grow during rest",
    "Progressive overload - increase weight gradually"
]

WORKOUT_TIPS = [
    "Warm up for 10 minutes before lifting",
    "Focus on form over heavy weights initially",
    "Breathe properly - exhale on effort",
    "Stretch after every workout for 10 minutes",
    "Track your weights and aim to increase gradually",
    "Rest 48 hours between training same muscle group",
    "Stay hydrated during workouts",
    "Mind-muscle connection is key"
]

# Main App
def main():
    st.markdown('<div class="main-header">💪 Your Personal Fitness & Nutrition Coach</div>', unsafe_allow_html=True)
    
    # Calculate progress
    days_elapsed = (datetime.now() - st.session_state.start_date).days
    days_remaining = GOAL_PERIOD - days_elapsed
    progress_percent = (days_elapsed / GOAL_PERIOD) * 100 if days_elapsed <= GOAL_PERIOD else 100
    
    # Top metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Current Weight", f"{st.session_state.current_weight} kg", 
                 f"{st.session_state.current_weight - CURRENT_WEIGHT:.1f} kg")
    with col2:
        st.metric("Target Weight", f"{TARGET_WEIGHT} kg")
    with col3:
        st.metric("To Lose", f"{st.session_state.current_weight - TARGET_WEIGHT:.1f} kg")
    with col4:
        st.metric("Days Elapsed", f"{days_elapsed} days")
    with col5:
        st.metric("Days Remaining", f"{max(0, days_remaining)} days")
    
    # Progress bar
    st.progress(min(progress_percent / 100, 1.0))
    st.markdown(f"**Progress: {min(progress_percent, 100):.1f}% Complete**")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📅 Today's Plan", "🍽️ Full Meal Plan", "💪 Workout Details", 
        "📊 Progress Tracker", "🔔 Notifications", "📚 Guidelines"
    ])
    
    with tab1:
        show_todays_plan()
    
    with tab2:
        show_full_meal_plan()
    
    with tab3:
        show_workout_details()
    
    with tab4:
        show_progress_tracker()
    
    with tab5:
        show_notifications()
    
    with tab6:
        show_guidelines()

def show_todays_plan():
    st.markdown('<div class="sub-header">📅 Today\'s Complete Schedule</div>', unsafe_allow_html=True)
    
    today = datetime.now().strftime("%A")
    current_time = datetime.now().strftime("%H:%M")
    
    st.info(f"**Today is {today}** | Current Time: {current_time}")
    
    # Today's Workout
    st.markdown("### 💪 Today's Workout")
    workout = WORKOUT_PLAN.get(today, {})
    
    if workout:
        st.markdown(f"**Focus: {workout['focus']}**")
        
        workout_df = pd.DataFrame(workout['exercises'])
        st.table(workout_df)
        
        st.markdown(f"**Cardio:** {workout['cardio']}")
        
        if st.button(f"✅ Mark {today}'s Workout Complete"):
            date_key = datetime.now().strftime('%Y-%m-%d')
            st.session_state.workout_completed[date_key] = today
            st.success(f"Great job! {today}'s workout marked complete! 🎉")
    
    st.markdown("---")
    
    # Today's Meals
    st.markdown("### 🍽️ Today's Meal Schedule")
    
    for meal_time, meal_info in MEAL_PLAN.items():
        with st.expander(f"**{meal_time}** - {meal_info['purpose']}", expanded=False):
            st.markdown(f"**Calories:** {meal_info['calories']} | **Protein:** {meal_info['protein']}g")
            for item in meal_info['items']:
                st.markdown(f"- {item}")
            
            if st.checkbox(f"Completed {meal_time}", key=f"meal_{meal_time}"):
                date_key = f"{datetime.now().strftime('%Y-%m-%d')}_{meal_time}"
                st.session_state.meals_completed[date_key] = True
    
    # Daily summary
    total_calories = sum(meal['calories'] for meal in MEAL_PLAN.values())
    total_protein = sum(meal['protein'] for meal in MEAL_PLAN.values())
    
    st.markdown("---")
    st.markdown("### 📊 Daily Nutrition Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Calories", f"{total_calories} kcal")
    with col2:
        st.metric("Total Protein", f"{total_protein}g")
    with col3:
        st.metric("Target", f"{DAILY_CALORIES} kcal")

def show_full_meal_plan():
    st.markdown('<div class="sub-header">🍽️ Complete 3-Month Meal Plan</div>', unsafe_allow_html=True)
    
    st.markdown("""
    This meal plan is designed to:
    - Create a caloric deficit for fat loss (300-500 calories below maintenance)
    - Provide sufficient protein for muscle building (150g daily)
    - Maintain energy for intense workouts
    - Support recovery and muscle growth
    """)
    
    for meal_time, meal_info in MEAL_PLAN.items():
        st.markdown(f'<div class="meal-card">', unsafe_allow_html=True)
        st.markdown(f"### {meal_time}")
        st.markdown(f"**Purpose:** {meal_info['purpose']}")
        st.markdown(f"**Nutrition:** {meal_info['calories']} calories | {meal_info['protein']}g protein")
        st.markdown("**Items:**")
        for item in meal_info['items']:
            st.markdown(f"- {item}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🔄 Weekly Variations")
    st.markdown("""
    **Alternate Protein Sources:**
    - Chicken can be replaced with: Fish, Turkey, Lean beef, Eggs
    - Paneer can be replaced with: Tofu, Tempeh, Greek yogurt, Cottage cheese
    
    **Alternate Carbs:**
    - Brown rice can be replaced with: Quinoa, Sweet potato, Whole wheat pasta
    - Chapati can be replaced with: Whole grain bread, Oats, Brown rice
    
    **Snack Alternatives:**
    - Fruits: Apple, Orange, Banana, Berries, Papaya
    - Nuts: Almonds, Walnuts, Cashews, Peanuts (limited quantity)
    """)

def show_workout_details():
    st.markdown('<div class="sub-header">💪 Complete Workout Program</div>', unsafe_allow_html=True)
    
    st.markdown("""
    This program focuses on:
    - Building chest, arms, and back as per your goals
    - Progressive overload for muscle growth
    - Balanced training for all muscle groups
    - Adequate cardio for fat loss
    """)
    
    # Week selector
    week_num = st.selectbox("Select Week to View", 
                            ["Week 1-4 (Foundation)", "Week 5-8 (Building)", "Week 9-12 (Peak)"])
    
    if "Week 1-4" in week_num:
        st.info("🎯 **Focus:** Learn proper form, build base strength, moderate weights")
    elif "Week 5-8" in week_num:
        st.info("🎯 **Focus:** Increase weights by 5-10%, focus on mind-muscle connection")
    else:
        st.info("🎯 **Focus:** Peak performance, maximum intensity, push your limits")
    
    # Show all days
    for day, workout in WORKOUT_PLAN.items():
        st.markdown(f'<div class="workout-card">', unsafe_allow_html=True)
        st.markdown(f"### {day} - {workout['focus']}")
        
        # Create DataFrame for exercises
        df = pd.DataFrame(workout['exercises'])
        st.table(df)
        
        st.markdown(f"**Cardio:** {workout['cardio']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📈 Progressive Overload Strategy")
    st.markdown("""
    - **Weeks 1-4:** Focus on form, use moderate weights you can control
    - **Weeks 5-8:** Increase weights by 5-10% on compound movements
    - **Weeks 9-12:** Push for new personal records, add intensity techniques
    
    **Important Notes:**
    - Always warm up properly (10 minutes cardio + dynamic stretching)
    - Cool down and stretch after every workout (10 minutes)
    - If you can do more than the max reps easily, increase weight
    - Rest is crucial - don't train same muscle group on consecutive days
    """)

def show_progress_tracker():
    st.markdown('<div class="sub-header">📊 Progress Tracking & Analytics</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚖️ Log Today's Weight")
        new_weight = st.number_input("Enter your weight (kg)", 
                                     min_value=60.0, max_value=90.0, 
                                     value=st.session_state.current_weight, step=0.1)
        
        if st.button("Update Weight"):
            today = datetime.now().strftime('%Y-%m-%d')
            st.session_state.weight_log[today] = new_weight
            st.session_state.current_weight = new_weight
            st.success(f"Weight updated to {new_weight} kg! Keep going! 💪")
    
    with col2:
        st.markdown("### 📈 Current Stats")
        weight_lost = CURRENT_WEIGHT - st.session_state.current_weight
        remaining_loss = st.session_state.current_weight - TARGET_WEIGHT
        
        st.metric("Total Weight Lost", f"{weight_lost:.1f} kg", 
                 f"{(weight_lost/4.5)*100:.1f}% of goal")
        st.metric("Remaining to Lose", f"{remaining_loss:.1f} kg")
        
        expected_loss = WEEKLY_LOSS * ((datetime.now() - st.session_state.start_date).days / 7)
        if weight_lost >= expected_loss:
            st.success("🎉 You're on track or ahead!")
        else:
            st.warning("⚠️ Need to push harder on diet and cardio")
    
    # Weight chart
    if len(st.session_state.weight_log) > 1:
        st.markdown("### 📉 Weight Progress Chart")
        
        dates = list(st.session_state.weight_log.keys())
        weights = list(st.session_state.weight_log.values())
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=weights, mode='lines+markers',
                                name='Actual Weight', line=dict(color='#FF4B4B', width=3)))
        
        # Add target line
        target_dates = [dates[0], (st.session_state.start_date + timedelta(days=GOAL_PERIOD)).strftime('%Y-%m-%d')]
        target_weights = [CURRENT_WEIGHT, TARGET_WEIGHT]
        fig.add_trace(go.Scatter(x=target_dates, y=target_weights, mode='lines',
                                name='Target', line=dict(color='#1F77B4', width=2, dash='dash')))
        
        fig.update_layout(title='Weight Loss Journey',
                         xaxis_title='Date',
                         yaxis_title='Weight (kg)',
                         hovermode='x unified')
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Workout completion
    st.markdown("### 💪 Workout Completion")
    completed_days = len(st.session_state.workout_completed)
    total_days = (datetime.now() - st.session_state.start_date).days
    completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0
    
    st.metric("Workouts Completed", f"{completed_days} days", 
             f"{completion_rate:.1f}% completion rate")
    
    if completion_rate >= 80:
        st.success("🔥 Excellent consistency!")
    elif completion_rate >= 60:
        st.info("👍 Good job, but room for improvement")
    else:
        st.warning("⚠️ Need more consistency for best results")

def show_notifications():
    st.markdown('<div class="sub-header">🔔 Daily Notification Schedule</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Set these reminders on your phone to stay on track throughout the day.
    You can use any reminder app or alarm app to set these up.
    """)
    
    current_time = datetime.now().strftime("%H:%M")
    
    for time, notification in NOTIFICATIONS.items():
        is_current = time == current_time[:5]
        
        if is_current:
            st.markdown(f'<div class="notification-box">', unsafe_allow_html=True)
            st.markdown(f"### 🔔 **RIGHT NOW** - {time}")
            st.markdown(f"## {notification}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"**{time}** - {notification}")
    
    st.markdown("---")
    st.markdown("### 📱 How to Set Up Notifications")
    st.markdown("""
    1. Use your phone's built-in Clock/Alarms app
    2. Set recurring daily alarms for each time above
    3. Label each alarm with the notification message
    4. OR use apps like Google Calendar, Microsoft To Do, or Any.do
    5. Set notifications 5 minutes before meal times as reminders
    """)

def show_guidelines():
    st.markdown('<div class="sub-header">📚 Essential Guidelines & Tips</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🥗 Nutrition Guidelines")
        for tip in NUTRITION_TIPS:
            st.markdown(f"- {tip}")
        
        st.markdown("---")
        st.markdown("### ⚠️ Foods to AVOID")
        avoid_foods = [
            "Sugar and sweets (chocolates, candies, ice cream)",
            "Fried foods (pakoras, samosas, chips)",
            "Processed foods (biscuits, instant noodles)",
            "Soft drinks and fruit juices (high sugar)",
            "White bread and refined flour products",
            "High-fat dairy (full cream milk, butter in excess)",
            "Alcohol (empty calories)",
            "Late night snacking after 10 PM"
        ]
        for food in avoid_foods:
            st.markdown(f"- ❌ {food}")
    
    with col2:
        st.markdown("### 💪 Workout Guidelines")
        for tip in WORKOUT_TIPS:
            st.markdown(f"- {tip}")
        
        st.markdown("---")
        st.markdown("### 🎯 Key Success Factors")
        success_factors = [
            "Consistency > Perfection (80% adherence is success)",
            "Track everything - weight, meals, workouts",
            "Take progress photos every 2 weeks",
            "Measure body parts monthly (chest, arms, waist)",
            "Sleep 7-8 hours daily",
            "Manage stress - it affects results",
            "Be patient - visible results in 4-6 weeks",
            "Join a gym partner for accountability"
        ]
        for factor in success_factors:
            st.markdown(f"- ✅ {factor}")
    
    st.markdown("---")
    st.markdown("### 📅 Monthly Milestones")
    
    milestones = {
        "Month 1 (Days 1-30)": {
            "Weight Target": "72.5 kg (-2.0 kg)",
            "Focus": "Building habit, learning form, initial fat loss",
            "Expectations": "Initial water weight loss, feeling energetic"
        },
        "Month 2 (Days 31-60)": {
            "Weight Target": "71.0 kg (-1.5 kg)",
            "Focus": "Muscle definition starts showing, strength increases",
            "Expectations": "Clothes fit better, visible chest and arm development"
        },
        "Month 3 (Days 61-90)": {
            "Weight Target": "70.0 kg (-1.0 kg)",
            "Focus": "Peak performance, final push, maintenance planning",
            "Expectations": "Clear muscle definition, significant transformation"
        }
    }
    
    for month, details in milestones.items():
        st.markdown(f"#### {month}")
        for key, value in details.items():
            st.markdown(f"**{key}:** {value}")
        st.markdown("")

# Run the app
if __name__ == "__main__":
    main()
