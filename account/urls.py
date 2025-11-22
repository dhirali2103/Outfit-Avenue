from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    # User registration
    path('register/', views.register, name='register'),
    # User login
    path('login/', views.user_login, name='login'),
    # User logout
    path('logout/', views.user_logout, name='logout'),
    # Email verification
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    # Registration OTP verification & resend
    path('verify-email-otp/', views.verify_email_otp, name='verify_email_otp'),
    path('resend-registration-otp/', views.resend_registration_otp, name='resend_registration_otp'),
    # Password reset
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    # Social logins
    path('social/google/', views.google_login, name='google_login'),
    path('social/google/callback/', views.google_callback, name='google_callback'),
    path('social/facebook/', views.facebook_login, name='facebook_login'),
    path('social/facebook/callback/', views.facebook_callback, name='facebook_callback'),
    # Login OTP verification & resend (MFA)
    path('verify-login-otp/', views.verify_login_otp, name='verify_login_otp'),
    path('resend-login-otp/', views.resend_login_otp, name='resend_login_otp'),
    # JWT token endpoints
    path('api/token/', views.jwt_token_obtain_pair, name='token_obtain_pair'),
    path('api/token/refresh/', views.jwt_token_refresh, name='token_refresh'),
    path('api/token/verify/', views.jwt_token_verify, name='token_verify'),
    # Orders page
    path('orders/', views.user_orders, name='orders'),
    # Profile page
    path('profile/', views.profile, name='profile'),
]