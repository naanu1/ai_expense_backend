import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Configure the generation parameters
generation_config = {
    "temperature": 0.7,  # Lowered for more predictable output
    "top_p": 0.9,
    "top_k": 50,
    "max_output_tokens": 300,
    "response_mime_type": "text/plain",
}

# Initialize the generative model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

def voice_llm(details, entry_method):
    # Crafting a clear and precise prompt to align with the business logic
    message = (
        f"Analyze the following statement and extract financial transactions only:\n"
        f"\"{details}\"\n\n"
        "For each valid transaction, provide:\n"
        "1. 'transaction_type' (either 'expense' or 'income').\n"
        "2. 'amount' (numeric value without currency symbols).\n"
        "3. 'description' (brief description of the transaction).\n"
        "4. 'entry_method' (use the provided entry method).\n\n"
        f"Use this entry method: '{entry_method}'.\n\n"
        "Respond with a JSON array containing only the valid financial transactions. "
        "If no valid transactions are found, return an empty JSON array [].\n"
        "IMPORTANT: Do not include any explanations or extra text—just the JSON."
    )

    # Start a chat session with the model
    chat_session = model.start_chat(history=[])

    # Send the message and get the response
    response = chat_session.send_message(message)

    try:
        # Attempt to parse the response as JSON
        result = json.loads(response.text)
        print(result)
    except json.JSONDecodeError:
        # Handle cases where the response is not valid JSON
        print("Error: Received invalid JSON from the model.")
        result = []

    return result

# # Test the function with sample input
# a = ("I bought a TV for 2 lakh")
# b = "voice"

# # Get the result from the voicellm function
# result = voicellm(a, b)

# # Print the result and its type
# print(result)
# print(type(result))
