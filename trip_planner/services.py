import json
import re
import logging
from ai_engine.services import get_groq_client
from django.conf import settings

logger = logging.getLogger(__name__)

def generate_trip_plan(destination, duration_days, budget, group_type, preferences):
    """Generate an AI-powered trip itinerary and budget estimation."""
    client = get_groq_client()
    
    if not client:
        return _fallback_trip_plan(destination, duration_days, budget)

    prompt = f"""You are an AI Travel Planner and Scam Prevention Expert.
Plan a trip to {destination} for {duration_days} days.
Budget: {budget} INR
Group Type: {group_type}
Preferences: {preferences}

Important:
1. Ensure the trip avoids common tourist scams and highlights safe areas.
2. Provide a daily itinerary.
3. Provide a realistic budget breakdown.
4. Give a minimum and luxury budget estimate.

Respond strictly in this JSON format:
{{
    "itinerary": [
        {{
            "day": 1,
            "description": "Arrival and local exploration",
            "activities": [
                {{"time": "09:00 AM - 11:00 AM", "title": "Visit Waterfall", "description": "Safe, scenic spot", "cost_estimate": 100}}
            ]
        }}
    ],
    "budget_analysis": {{
        "hotel_cost": 2000,
        "food_cost": 1500,
        "transport_cost": 1000,
        "activities_cost": 500,
        "emergency_buffer": 1000,
        "minimum_budget": 4500,
        "luxury_budget": 12000
    }},
    "travel_routes": [
        {{"source": "Airport/Station", "destination": "Hotel", "mode": "Taxi", "distance_km": 15, "time_mins": 30, "cost": 500}}
    ],
    "safety_recommendations": [
        "Use prepaid taxis to avoid overcharging."
    ]
}}
"""

    try:
        response = client.chat.completions.create(
            model=getattr(settings, 'AI_MODEL', 'llama-3.3-70b-versatile'),
            messages=[
                {"role": "system", "content": "You are a smart AI travel planner and scam safety expert. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=2500,
        )

        result_text = response.choices[0].message.content.strip()
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(result_text)

        return result
    except Exception as e:
        logger.error(f"AI trip generation failed: {e}")
        return _fallback_trip_plan(destination, duration_days, budget)

def _fallback_trip_plan(destination, duration_days, budget):
    """Fallback if AI is unavailable."""
    budget_val = float(budget)
    daily = budget_val / duration_days
    
    itinerary = []
    for d in range(1, duration_days + 1):
        itinerary.append({
            "day": d,
            "description": f"Explore {destination} Day {d}",
            "activities": [
                {"time": "10:00 AM - 01:00 PM", "title": "Local Sightseeing", "description": "Check local safe spots", "cost_estimate": 200},
                {"time": "02:00 PM - 05:00 PM", "title": "Cultural Activity", "description": "Enjoy local culture safely", "cost_estimate": 300}
            ]
        })
        
    return {
        "itinerary": itinerary,
        "budget_analysis": {
            "hotel_cost": daily * 0.4 * duration_days,
            "food_cost": daily * 0.3 * duration_days,
            "transport_cost": daily * 0.2 * duration_days,
            "activities_cost": daily * 0.1 * duration_days,
            "emergency_buffer": budget_val * 0.1,
            "minimum_budget": budget_val * 0.7,
            "luxury_budget": budget_val * 2.0
        },
        "travel_routes": [],
        "safety_recommendations": ["Avoid unverified vendors", "Always ask for price upfront"]
    }
