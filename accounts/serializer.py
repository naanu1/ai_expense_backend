from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User,Transaction
from django.utils.encoding import smart_str,force_bytes,DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .utils import Util

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={'input_type':'password'},write_only=True)
    password2 = serializers.CharField(style={'input_type':'password'},write_only=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'phone_number', 'gender', 'password', 'password2']
        extra_kwargs={'password':{'write_only':True}}

    def validate(self, data):
        print("data in seri",data)
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        validate_password(data['password'])  # Validates password strength
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255,)
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['email','password']
   


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        max_length=255, style={'input_type': 'password'}, write_only=True
    )
    new_password = serializers.CharField(
        max_length=255, style={'input_type': 'password'}, write_only=True
    )
    confirm_new_password = serializers.CharField(
        max_length=255, style={'input_type': 'password'}, write_only=True
    )

    class Meta:
        model = User
        fields = ['current_password', 'new_password', 'confirm_new_password']

    def validate(self, data):
        user = self.context.get('user')

        # Verify the current password is correct
        if not user.check_password(data['current_password']):
            raise serializers.ValidationError({"current_password": "Incorrect current password."})

        # Check if new passwords match
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})

        # Validate password strength
        validate_password(data['new_password'])

        return data
    

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, data):
        self.token = data['refresh']
        return data

    def save(self, **kwargs):
        RefreshToken(self.token).blacklist()

class ResetEmailNewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        model = User
        fields = ['email']
    def validate(self, attrs):
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            link = f'http://localhost:3000/reset-password/{urlsafe_base64_encode(force_bytes(user.pk))}/{token}'
            print(f'Generated password reset link for {email}: {link}')  # Added logging

            data = {
                'subject': 'Reset Your Password',
                'body': f'Click the following link to reset your password: {link}',
                'to_email': user.email,
            }

            Util.send_email(data)  # Make sure the email sending works
            return attrs
        else:
            print(f"User with email {email} does not exist.")  # Added logging
            raise serializers.ValidationError("You are not a registered user.")


        
class UserPasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        max_length=255, style={'input_type': 'password'}, write_only=True
    )
    confirm_new_password = serializers.CharField(
        max_length=255, style={'input_type': 'password'}, write_only=True
    )

    class Meta:
        model = User
        fields = ['new_password', 'confirm_new_password']

    def validate(self, data):
        try:
            uid=self.context.get('uid')
            token=self.context.get('token')
            id=smart_str(urlsafe_base64_decode(uid))
            user=User.objects.get(id=id) 

            if not PasswordResetTokenGenerator().check_token(user,token):
                raise serializers.ValidationError("Token is not Valid or expired")
            
            if data['new_password'] != data['confirm_new_password']:
                raise serializers.ValidationError({"new_password": "Passwords do not match."})
            
            validate_password(data['new_password'])
            user.set_password(data['new_password'])
            user.save()
            return data
        except DjangoUnicodeDecodeError as identifier:
            PasswordResetTokenGenerator().check_token(user,token)
            raise serializers.ValidationError("Token is not Valid or expired")   
       

""" data with transaction"""

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields =[ 'id','transaction_type', 'amount', 'description', 'entry_method','timestamp']

    def create(self, validated_data):
        # If user is in context, set it
        validated_data['user'] = self.context['request'].user
        return Transaction.objects.create(**validated_data)




















# class ResetPasswordSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     otp = serializers.CharField()
#     new_password = serializers.CharField(write_only=True)
#     confirm_password = serializers.CharField(write_only=True)

#     def validate(self, data):
#         if data['new_password'] != data['confirm_password']:
#             raise serializers.ValidationError({"password": "Passwords do not match."})
#         validate_password(data['new_password'])  # Validates new password
#         return data
    

    # def validate(self, attrs):
    #     email = attrs.get('email')

    #     if User.objects.filter(email=email).exists():
    #         user = User.objects.get(email=email)

    #         # Generate encoded user ID and reset token
    #         uid = urlsafe_base64_encode(force_bytes(user.id))
    #         token = PasswordResetTokenGenerator().make_token(user)

    #         # Generate password reset link
    #         link = f'http://localhost:3000/api/reset/{uid}/{token}'
    #         print(link)
    #         # Email data
    #         data = {
    #             'subject': 'Reset Your Password',
    #             'body': f'Click the following link to reset your password: {link}',
    #             'to_email': user.email,
    #         }

    #         # Send email using Util class
    #         Util.send_email(data)  # Fixed method call

    #         return attrs

    #     else:
    #         raise serializers.ValidationError("You are not a registered user.")

# class LoginSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField(write_only=True)
#     class Meta:
#         model = User
#         fields = ['email','password']    

#     def validate(self, data):
#         user = authenticate(**data)
#         if not user:
#             raise serializers.ValidationError({"detail": "Invalid email or password."})
#         return user