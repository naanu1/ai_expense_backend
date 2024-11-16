from django.urls import path
from .views import Aitransactions, RegisterView, LoginView, LogoutView,ChangePasswordView,ResetEmailNewPasswordView,UserPasswordResetView,add_transaction, delete_transaction, transaction_history, upload_image,manual_transactions,chatdb

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    # path('send-otp/', SendOTPView.as_view(), name='send_otp'),
    path('reset-password/', ResetEmailNewPasswordView.as_view(), name='email-reset_password'),
    # path('reset-password/<uid>/<token>/', UserPasswordResetView.as_view(), name='reset_password'),
    path('reset-password/<uid>/<token>/', UserPasswordResetView.as_view(), name='reset_password'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('transactions/', add_transaction, name='add_transaction'),
    path('transactions/history/', transaction_history, name='transaction_history'),
    path('transactions/delete/<int:transaction_id>/', delete_transaction, name='delete_transaction'),
    path('aitransactions/', Aitransactions.as_view(), name='ai_add_transaction'),
    path('itransactions/', upload_image, name='image_transaction'),
    path('mtransactions/', manual_transactions, name='manual_transaction'),
    path('chat-with-db/', chatdb, name='chat_with_db'),
]
