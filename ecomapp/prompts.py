import openai
import json
import os
from openai import OpenAI
import re

DEEPSEEK_API_KEY = "sk-3a7ee5ee25384361920641460e5b2b2a"


client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


def identify_subcategories(user_message, available_subcategories):
    prompt = f"""
            You are a smart shopping assistant.

            Given the user message:
            "{user_message}"

            And the available subcategories:
            {available_subcategories}

            Identify the relevant subcategories and respond in the following JSON format and btw it could be more than 2 items so this just an example with 2 output to see the desired output:
            {{
                "product1": "pizza",
                "product2": "tshirt"
            }}

            Only include categories that match the message content.
            If the product does not belong to any of the subcategories, just return: "does not exist"
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
    You are a smart shopping assistant.

    This is the user message:
    "{user_message}"
    
    Here is a mapping of available product titles per subcategory:
    {subcategory_product_titles}
    
    Pick one best-fitting product for each subcategory, based on the message and make sure to either put the key as "product" if the desired product is not a food or "food_product" if the desired product is a food from the message btw it could be more than 2 items so this just an example with 2 output to see the desired output.
    
    Respond in JSON format like this:
    {{
        "food_product": "pepperoni pizza",
        "product": "oversized cotton t-shirt"
    }}
    Only pick one per subcategory, and ensure it's semantically aligned with the user's message.
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
