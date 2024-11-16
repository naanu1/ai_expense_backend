import google.generativeai as genai
import os 
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
def get_db_schema():
    return """
    Model: Transaction
    Fields:
    - user (ForeignKey to User)
    - transaction_type (CharField: 'expense' or 'income')
    - amount (DecimalField)
    - description (CharField)
    - entry_method (CharField: 'manual', 'voice', or 'image')
    - timestamp (DateTimeField)
    
    Note: All queries must filter by user_id for security and if user query is asking about any  description always use django lookups __icontains
    """
def generate_query(user_question, user_id):
        prompt = f"""
        Given this database schema: {get_db_schema()}
        
        User Question: {user_question}
        User ID: {user_id}
        
        Create the most optimized Django ORM query to answer this question.
        The query MUST filter by user_id={user_id} for security.
        
        Return only the Python code for the query, nothing else.
        Use Transaction.objects as the base queryset.

        """
        
        response = model.generate_content(prompt)
        return response.text

def validate_response(query_result, user_question):
    prompt = f"""
    Question: {user_question}
    Data: {query_result}
    
    Provide a clear, natural language answer to the question based on this data.
    If the data doesn't answer the question properly, say so.
    Be concise but complete.
    """
    
    response = model.generate_content(prompt)
    return response.text

            
    