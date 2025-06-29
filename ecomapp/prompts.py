import openai
import json
import os
from openai import OpenAI
import re
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


def identify_subcategories(user_message, available_subcategories):
    prompt = f"""
You are a smart shopping assistant. The user message may come from a transcription of voice input, which may include repetition or slight errors — be smart in interpreting the intent.

## User Message:
\"\"\"{user_message}\"\"\"

## Available Subcategories:
{available_subcategories}

## Task:
- Identify relevant subcategories based on the user message.
- You may assign **the same subcategory to multiple products**.
- If the user's intent matches no available subcategory, return: "does not exist".
- Do not invent new subcategories — only use those from the provided list.

## Response Format:
Return **only valid JSON**, without any explanation or markdown:

Example:
{{
    "product1": "Maxi Dresses",
    "product2": "Maxi Dresses"
}}
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        stream=False,
    )

    message_content = response.choices[0].message.content.strip()

    if message_content.startswith("```json"):
        message_content = re.sub(r"```json\s*|\s*```", "", message_content).strip()

    try:
        return json.loads(message_content)
    except json.JSONDecodeError:
        return {"error": "Could not parse response", "raw": message_content}


def select_products(user_message, subcategory_product_titles):
    prompt = f"""
You are a smart shopping assistant. The user might send a voice message transcribed to text, which may include errors or repeated words. Your job is to understand what the user wants and return only matching product titles from the mapping below.

## User Message:
\"\"\"{user_message}\"\"\"

## Available products by subcategory:
{subcategory_product_titles}

## Instructions:
- Extract relevant product names from the user message.
- Match them with titles from the given mapping.
- Group matched products into:
    - "food_product" for food items
    - "product" for non-food items
- If a product doesn't belong to any subcategory, ignore it.
- Use only the product titles from the provided mapping — do not generate new ones.
- Return a valid **raw JSON** with no explanation, no comments, no markdown.

## Expected Output Format:
{{
    "food_product": ["Pizza Margherita", "Vegan Burger"],
    "product": ["Classic T-Shirt", "Smart Watch"]
}}
"""

    # Call the LLM
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        stream=False,
    )

    message_content = response.choices[0].message.content.strip()

    # Remove markdown code block if present
    if message_content.startswith("```json"):
        message_content = re.sub(r"```json\s*|\s*```", "", message_content).strip()

    # Try to parse the response as JSON
    try:
        return json.loads(message_content)
    except json.JSONDecodeError:
        return {
            "error": "Could not parse response. Raw output provided.",
            "raw": message_content,
        }
