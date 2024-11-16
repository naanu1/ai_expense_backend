import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Configure the generation parameters with increased token limit
generation_config = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 50,
    "max_output_tokens": 1000,  # Increased from 300
    "response_mime_type": "text/plain",
}

# Initialize the generative model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",  # Changed to pro-vision as it's better for image analysis
    generation_config=generation_config,
)

def process_image(image_path, entry_method):
    try:
        # Load the image
        image = Image.open(image_path)
        
        # Craft the prompt for image analysis with explicit length constraint
        prompt =("""
        Analyze this image and extract financial transactions only if this is a financial document (receipt, bill, invoice etc.).
        If this is not a financial document, return an empty array [].
        
        Extract only the main item transactions (ignore subtotal, tax, and total).
        
        For each transaction found, provide:
        1. 'transaction_type' (either 'expense' or 'income')
        2. 'amount' (numeric value without currency symbols)
        3. 'description' (brief description)"""
        f"Use this entry method: '{entry_method}'.\n\n"
        "Respond with only a JSON array. No additional text or explanations.")

        # Send the image and prompt to the model
        response = model.generate_content([prompt, image])
        
        try:
            # Extract the text content from the response
            response_text = response.text.strip()
            print("res_text",response_text)
            # Clean up the response text
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("[") and response_text.endswith("]"):
                response_text = response_text
            
            # Parse the JSON response
            result = json.loads(response_text)
            print("result",result)
            
            # Add entry_method to each transaction
            for transaction in result:
                transaction['entry_method'] = entry_method
                
            return result
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {str(e)}")
            print(f"Received response: {response_text}")
            return []
            
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return []

# Example usage:
result = process_image("backend/images/ai.webp", "image")
print(result)