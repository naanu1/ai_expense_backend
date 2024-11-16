from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .image_llm import process_image
from django.utils.dateparse import parse_datetime
from  .voice_llm import voice_llm
from django.db.models import Q
from .models import Transaction
from .serializer import (
   RegisterSerializer, LoginSerializer, LogoutSerializer,ChangePasswordSerializer,ResetEmailNewPasswordSerializer,UserPasswordResetSerializer,TransactionSerializer
)
from rest_framework.decorators import api_view, permission_classes
from accounts.renders import UserRenders
import random
import datetime
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from .chats import generate_query,validate_response

User = get_user_model()
otp_storage = {}

def get_token_for_user(user):
    refresh=RefreshToken.for_user(user)

    return{
        'refresh':str(refresh),
        'access':str(refresh.access_token),
    }

class RegisterView(APIView):
    renderer_classes=[UserRenders]
    def post(self, request):
        print("req in view",request)
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user=serializer.save()
            token=get_token_for_user(user)
            return Response({"token":token,"message": "Registration successful."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    renderer_classes=[UserRenders]
    def post(self, request):
        print(request.data)
        serializer = LoginSerializer(data=request.data)
    
        
        if serializer.is_valid():
            print("login serializer",serializer)
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user=authenticate(email=email,password=password)
            if user is not None:
                token=get_token_for_user(user)
                re=eval("Transaction.objects.filter(user__email='bitu@gmail.com', transaction_type='income').aggregate(total_income=Sum('amount'))['total_income']")
                print(re)
                return Response({"token":token,'msg':'Login Success'}, status=status.HTTP_200_OK)
            else:
                print("a3",serializer._errors)
                return Response({'errors':{'non_field_errors':['Email or Password is not valid']}}, status=status.HTTP_400_BAD_REQUEST)
        print("a2",serializer.errors)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  




class ChangePasswordView(APIView):
    renderer_classes = [UserRenders]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user  # Get the authenticated user
        serializer = ChangePasswordSerializer(data=request.data, context={'user': user})

        if serializer.is_valid():
            # If valid, set the new password
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            user.save()

            return Response(
                {'msg': 'Password changed successfully.'}, 
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LogoutView(APIView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Logout successful."}, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetEmailNewPasswordView(APIView):
    renderer_classes=[UserRenders]

    def post(self,request,format=None):
        serializer=ResetEmailNewPasswordSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "password reset link sent, please check your email"}, status=status.HTTP_200_OK) 
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserPasswordResetView(APIView):
    renderer_classes=[UserRenders]

    def post(self,request,uid,token,format=None):
        serializer=UserPasswordResetSerializer(data=request.data,context={
            'uid':uid,'token':token
        })
        if serializer.is_valid():
            return Response({"message": "password reset successfully"}, status=status.HTTP_204_NO_CONTENT) 
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
        
""" data with transactions """
class Aitransactions(APIView):
    renderer_classes = [UserRenders]

    def post(self, request):
        textual_info = request.data.get('textual_info')
        entry_method = request.data.get('entry_method')

        if not textual_info or not entry_method:
            return Response(
                {"error": "Textual information and entry method are required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        extracted_transactions = voice_llm(textual_info, entry_method)
        serializer = TransactionSerializer(
            data=extracted_transactions, many=True, context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
def upload_image(request):
    if 'image' not in request.FILES:
        return Response({"error": "No image uploaded."}, status=status.HTTP_400_BAD_REQUEST)

    image = request.FILES['image']
    entry_method = request.data.get('entry_method')

    if not entry_method:
        return Response(
            {"error": "Image and entry method are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Process the image with the Gemini-like function
    json_response = process_image(image, entry_method)
    
    # Serialize the response if needed
    serializer = TransactionSerializer(data=json_response, many=True, context={'request': request})

    if serializer.is_valid():
        serializer.save()
    
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   




@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
def add_transaction(request):
    # Check if the data is a list or a single object
    if isinstance(request.data, list):
        # If it's a list, we need to process each entry
        serializer = TransactionSerializer(data=request.data, many=True, context={'request': request})
    else:
        # Otherwise, treat it as a single transaction
        serializer = TransactionSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_history(request):
    user = request.user
    query = request.GET.get('query', '')
    amount = request.GET.get('amount')
    transaction_type = request.GET.get('transaction_type')
    entry_method = request.GET.get('entry_method')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    transactions = Transaction.objects.filter(user=user)

    # Full-text search
    if query:
        transactions = transactions.annotate(
            search=SearchVector('description', 'transaction_type', 'entry_method')
        ).filter(search=SearchQuery(query))

    # Filter by amount if provided
    if amount:
        transactions = transactions.filter(amount__gte=amount)

    # Filter by transaction type if provided
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    # Filter by entry method if provided
    if entry_method:
        transactions = transactions.filter(entry_method=entry_method)

    # Filter by date range if provided
    if start_date:
        transactions = transactions.filter(timestamp__date__gte=start_date)
    if end_date:
        transactions = transactions.filter(timestamp__date__lte=end_date)

    
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chatdb(req):
    print("request",req.data)
    question=req.data.get('question')
    user=req.user
    print(user)
    try:
        query_code=generate_query(question,user)
        print("query code",query_code)
        if 'email' not in query_code or 'Transaction.objects' not in query_code:
                    return Response({
                        'error': 'Invalid query generated'
                    }, status=400)
        import re
        query_code = query_code.strip()
        pattern = r"(?m)^`python\s*(.*?)\s*`$"
        cleaned_code = re.sub(pattern, r"\1", query_code, flags=re.DOTALL)
        cleaned_code = cleaned_code.strip() 
        if cleaned_code.startswith("```python"):
            cleaned_code = cleaned_code[9:]  
        if cleaned_code.endswith("```"):
            cleaned_code = cleaned_code[:-3] 

        try:
            result = eval(cleaned_code)
        except Exception as e:
            print("eval error ")
            print(e)    
        print("result",result)
        if hasattr(result, '__iter__'):
                    result = list(result.values())
                
            
        final_response = validate_response(result, question)
        print("final",final_response)
        return Response({
                    'answer': final_response,
                    'data': result,
                    'status':status.HTTP_200_OK
                })
    except Exception as e:
            return Response({
                'error': str(e)
            }, status=400)



# @api_view(['GET'])
# @permission_classes([IsAuthenticated])

# def get_trans(req):
#     try:
#         user=req.user
#         income=Transaction.objects.filter(user=user,transaction_type="income").aggregate(total_income=Sum('amount'))['total']
#         expense=Transaction.objects.filter(user=user,transaction_type="expense").aggregate(total_expense=Sum('amount'))['total']
#         balance=expense['total_expense']-income['total_income']
#         top_5=Transaction.objects.filter(user=user).order_by('-timestamp')[:5]




@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_transaction(request, transaction_id):
    try:
        # Ensure transaction belongs to the user
        transaction = Transaction.objects.get(id=transaction_id, user=request.user)
        transaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Transaction.DoesNotExist:
        return Response({"error": "Transaction not found or not authorized"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['post'])
@permission_classes([IsAuthenticated])
def manual_transactions(request):
    serializer = TransactionSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





# class SendOTPView(APIView):
#     def post(self, request):
#         email = request.data.get('email')
#         user = User.objects.filter(email=email).first()
#         if not user:
#             return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

#         otp = str(random.randint(100000, 999999))
#         expiry = datetime.datetime.now() + datetime.timedelta(minutes=3)
#         otp_storage[email] = {'otp': otp, 'expiry': expiry}

#         send_mail(
#             "Your OTP",
#             f"Your OTP is {otp}. It is valid for 3 minutes.",
#             "admin@example.com",
#             [email]
#         )
#         return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)


# class ResetPasswordView(APIView):
#     renderer_classes=[UserRenders]
#     def post(self, request):
#         serializer = ResetPasswordSerializer(data=request.data)
#         if serializer.is_valid():
#             email = serializer.validated_data['email']
#             otp = serializer.validated_data['otp']

#             if email in otp_storage and otp_storage[email]['otp'] == otp:
#                 if datetime.datetime.now() < otp_storage[email]['expiry']:
#                     user = User.objects.get(email=email)
#                     user.set_password(serializer.validated_data['new_password'])
#                     user.save()
#                     del otp_storage[email]
#                     return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
#                 else:
#                     return Response({"error": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)
#             return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class LoginView(APIView):
#     renderer_classes=[UserRenders]
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.validated_data
#             refresh = RefreshToken.for_user(user)
#             return Response({
#                 'refresh': str(refresh),
#                 'access': str(refresh.access_token),
#                 'message': 'Login successful.'
#             }, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)