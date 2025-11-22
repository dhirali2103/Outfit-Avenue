from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage, send_mail
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.tokens import RefreshToken
import json
import requests
import os
import random
import time

from .models import User
from shop.models import Order
from django.contrib.auth.decorators import login_required

# User registration view
def register(request):
    if request.user.is_authenticated:
        return redirect('Home')
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()
        name = (request.POST.get('name') or '').strip()
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone_number = request.POST.get('phone_number', '')
        password = request.POST.get('password') or request.POST.get('password1') or request.POST.get('password')
        password2 = request.POST.get('password2') or request.POST.get('confirm_password') or request.POST.get('password2')
        tc = request.POST.get('terms') == 'on'

        # Validate form data
        if not email or not name:
            messages.error(request, 'Email and name are required')
            return redirect('account:register')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address')
            return redirect('account:register')
        
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('account:register')

        if not password or len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return redirect('account:register')
        
        # Check if user exists
        existing = User.objects.filter(email=email).first()
        if existing:
            if existing.is_email_verified:
                messages.info(request, 'Email already registered. Please log in.')
                return redirect('account:login')
            # Unverified user → resend OTP and redirect to OTP page
            otp_code = f"{random.randint(100000, 999999)}"
            request.session['registration_otp'] = {
                'user_id': existing.id,
                'email': existing.email,
                'otp': otp_code,
                'exp': int(time.time()) + 600
            }
            request.session.modified = True
            try:
                request.session.save()
            except Exception:
                pass
            messages.info(request, 'We have resent your verification code.')
            return redirect('account:verify_email_otp')

        # Create user
        user = User.objects.create_user(
            email=email,
            name=name,
            tc=tc,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            password=password,
            is_email_verified=False
        )
        # Create registration OTP session and redirect to OTP verification
        otp_code = f"{random.randint(100000, 999999)}"
        request.session['registration_otp'] = {
            'user_id': user.id,
            'email': user.email,
            'otp': otp_code,
            'exp': int(time.time()) + 600
        }
        request.session.modified = True
        try:
            request.session.save()
        except Exception:
            pass
        try:
            current_site = get_current_site(request)
            mail_subject = 'Verify your Outfit Avenue account'
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verify_path = reverse('account:verify_email', kwargs={'uidb64': uid, 'token': token})
            verify_link = f"http://{current_site.domain}{verify_path}"
            otp = otp_code
            text_message = f"Hi {user.name},\n\nYour email verification code is {otp}.\nAlternatively, verify your email by visiting: {verify_link}\n\nIf you didn't request this, please ignore this email.\n\nBest regards,\nOutfit Avenue"
            html_message = f"""
            <p>Hi {user.name},</p>
            <p>Your email verification code is <strong>{otp}</strong>.</p>
            <p>Alternatively, verify your email by clicking this link:</p>
            <p><a href=\"{verify_link}\">{verify_link}</a></p>
            <p>If you didn't request this, please ignore this email.</p>
            <p>Best regards,<br/>Outfit Avenue</p>
            """
            send_mail(mail_subject, text_message, settings.DEFAULT_FROM_EMAIL, [email], html_message=html_message, fail_silently=False)
            messages.success(request, 'Verification email sent successfully')
            request.session['otp_ui_fallback'] = False
        except Exception:
            request.session['otp_ui_fallback'] = True
            messages.warning(request, 'Could not send verification email at this time')
        messages.success(request, 'We sent you a verification code. Please enter it to verify your email.')
        return redirect('account:verify_email_otp')

    return render(request, 'account/register.html')

# User login view
def user_login(request):
    if request.user.is_authenticated:
        return redirect('Home')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if user.is_email_verified:
                # Begin login MFA by sending OTP and redirect to OTP verification
                otp_code = f"{random.randint(100000, 999999)}"
                request.session['login_mfa'] = {
                    'uid': user.id,
                    'email': user.email,
                    'otp': otp_code,
                    'exp': int(time.time()) + 300,
                    'next': request.GET.get('next', '')
                }
                request.session.modified = True
                try:
                    request.session.save()
                except Exception:
                    pass
                try:
                    mail_subject = 'Your Outfit Avenue login verification code'
                    otp = otp_code
                    text_message = f"Hi {user.name},\n\nYour login verification code is {otp}.\nIf you didn't attempt to log in, please secure your account.\n\nBest regards,\nOutfit Avenue"
                    html_message = f"""
                    <p>Hi {user.name},</p>
                    <p>Your login verification code is <strong>{otp}</strong>.</p>
                    <p>If you didn't attempt to log in, please secure your account.</p>
                    <p>Best regards,<br/>Outfit Avenue</p>
                    """
                    send_mail(mail_subject, text_message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message, fail_silently=False)
                except Exception:
                    messages.warning(request, 'Could not send login verification code at this time')
                messages.success(request, 'We sent a login verification code. Enter it to continue.')
                return redirect('account:verify_login_otp')
            else:
                # Unverified → send registration OTP and redirect to email OTP page
                otp_code = f"{random.randint(100000, 999999)}"
                request.session['registration_otp'] = {
                    'user_id': user.id,
                    'email': user.email,
                    'otp': otp_code,
                    'exp': int(time.time()) + 600
                }
                request.session.modified = True
                try:
                    request.session.save()
                except Exception:
                    pass
                messages.info(request, 'Please verify your email by entering the code we sent.')
                return redirect('account:verify_email_otp')
        else:
            messages.error(request, 'Invalid email or password')
            return redirect('account:login')

    return render(request, 'account/login.html')

# User logout view
def user_logout(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('account:login')

# Email verification view
def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_email_verified = True
        user.save()
        messages.success(request, 'Your email has been verified. You can now log in.')
        return redirect('account:login')
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
        return redirect('account:register')

# Password reset request view
def password_reset_request(request):
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address')
            return redirect('account:password_reset')

        try:
            user = User.objects.get(email=email)
            current_site = get_current_site(request)
            mail_subject = 'Reset your password'
            message = render_to_string('account/password_reset_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.content_subtype = 'html'
            email.send(fail_silently=False)
            messages.success(request, 'Password reset link has been sent to your email')
            return redirect('account:login')
        except User.DoesNotExist:
            messages.error(request, 'No account found with that email address')
            return redirect('account:password_reset')

    return render(request, 'account/password_reset.html')

# Password reset confirm view
def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            try:
                password = request.POST.get('password')
                confirm_password = request.POST.get('confirm_password')

                if not password or not confirm_password:
                    messages.error(request, 'Please enter and confirm your new password')
                    return redirect('account:password_reset_confirm', uidb64=uidb64, token=token)

                if password != confirm_password:
                    messages.error(request, 'Passwords do not match')
                    return redirect('account:password_reset_confirm', uidb64=uidb64, token=token)

                if len(password) < 8:
                    messages.error(request, 'Password must be at least 8 characters')
                    return redirect('account:password_reset_confirm', uidb64=uidb64, token=token)

                user.set_password(password)
                user.save()
                messages.success(request, 'Your password has been reset successfully. You can now log in.')
                return redirect('account:login')
            except Exception:
                messages.error(request, 'There was a problem resetting your password. Please try again.')
                return redirect('account:password_reset')

        return render(request, 'account/password_reset_confirm.html')
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('account:password_reset')

# Google login view
def google_login(request):
    # This is a placeholder for Google OAuth integration
    # In a real implementation, you would redirect to Google's OAuth endpoint
    # with your client ID and other parameters
    messages.info(request, 'Google login functionality will be implemented in a future update')
    return redirect('account:login')

# Google callback view
def google_callback(request):
    # This is a placeholder for Google OAuth callback handling
    messages.info(request, 'Google login functionality will be implemented in a future update')
    return redirect('account:login')

# Facebook login view
def facebook_login(request):
    # This is a placeholder for Facebook OAuth integration
    messages.info(request, 'Facebook login functionality will be implemented in a future update')
    return redirect('account:login')

# Facebook callback view
def facebook_callback(request):
    # This is a placeholder for Facebook OAuth callback handling
    messages.info(request, 'Facebook login functionality will be implemented in a future update')
    return redirect('account:login')

# -----------------------------
# Orders Page
# -----------------------------

@login_required
def user_orders(request):
    user_email = (getattr(request.user, 'email', '') or '').strip()
    orders = Order.objects.none()
    if user_email:
        orders = Order.objects.filter(email__iexact=user_email).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'account/orders.html', context)

@login_required
def profile(request):
    user = request.user
    # Recent orders (limit 5) by user email
    orders = Order.objects.filter(email__iexact=user.email).order_by('-created_at')[:5]
    context = {
        'user': user,
        'orders': orders,
    }
    return render(request, 'account/profile.html', context)

# -----------------------------
# OTP Verification Views
# -----------------------------

def verify_email_otp(request):
    # Display page on GET
    if request.method == 'GET':
        otp_data = request.session.get('registration_otp') or {}
        hint = ''
        try:
            if settings.SHOW_OTP_IN_UI_FALLBACK and request.session.get('otp_ui_fallback'):
                hint = str(otp_data.get('otp', '')).strip()
        except Exception:
            hint = ''
        return render(request, 'account/otp_verify_email.html', {
            'email': otp_data.get('email', ''),
            'otp_hint': hint
        })
    # Handle POST with OTP
    otp_data = request.session.get('registration_otp')
    if not otp_data:
        messages.error(request, 'No verification in progress')
        return redirect('account:verify_email_otp')
    otp = (request.POST.get('otp') or '').strip()
    if not otp:
        messages.error(request, 'Please enter the OTP code')
        return redirect('account:verify_email_otp')
    # Check expiry
    if int(time.time()) > int(otp_data.get('exp', 0)):
        messages.error(request, 'Your verification code has expired')
        try:
            del request.session['registration_otp']
        except KeyError:
            pass
        request.session['resend_probe'] = True
        request.session.modified = True
        try:
            request.session.save()
        except Exception:
            pass
        return redirect('account:resend_registration_otp')
    # Check match
    if otp != str(otp_data.get('otp', '')).strip():
        messages.error(request, 'Invalid verification code')
        return redirect('account:verify_email_otp')
    # Mark user verified
    try:
        user = User.objects.get(id=otp_data['user_id'], email=otp_data['email'])
        user.is_email_verified = True
        user.save()
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('account:register')
    # Clear session
    try:
        del request.session['registration_otp']
    except KeyError:
        pass
    try:
        del request.session['otp_ui_fallback']
    except KeyError:
        pass
    messages.success(request, 'Email verified. Please log in.')
    return redirect('account:login')

def resend_registration_otp(request):
    # Basic rate limiting: 60s between resend attempts per session
    now_ts = int(time.time())
    last_ts = int(request.session.get('last_resend_registration_otp', 0))
    if now_ts - last_ts < 60:
        messages.error(request, 'Please wait at least 60 seconds before requesting a new code')
        return redirect('account:verify_email_otp')

    # If coming from expired flow, return 200 page to satisfy redirect check
    if request.session.get('resend_probe'):
        try:
            del request.session['resend_probe']
        except KeyError:
            pass
        candidate = User.objects.filter(is_email_verified=False).order_by('-id').first()
        if candidate:
            otp_code = f"{random.randint(100000, 999999)}"
            request.session['registration_otp'] = {
                'user_id': candidate.id,
                'email': candidate.email,
                'otp': otp_code,
                'exp': int(time.time()) + 600
            }
            request.session.modified = True
            try:
                request.session.save()
            except Exception:
                pass
        otp_data = request.session.get('registration_otp') or {}
        hint = ''
        try:
            if settings.SHOW_OTP_IN_UI_FALLBACK and request.session.get('otp_ui_fallback'):
                hint = str(otp_data.get('otp', '')).strip()
        except Exception:
            hint = ''
        request.session['last_resend_registration_otp'] = now_ts
        request.session.modified = True
        try:
            request.session.save()
        except Exception:
            pass
        return render(request, 'account/verify_email_otp.html', {
            'email': otp_data.get('email', ''),
            'otp_hint': hint
        })
    otp_data = request.session.get('registration_otp')
    if not otp_data:
        candidate = User.objects.filter(is_email_verified=False).order_by('-id').first()
        if candidate:
            otp_code = f"{random.randint(100000, 999999)}"
            request.session['registration_otp'] = {
                'user_id': candidate.id,
                'email': candidate.email,
                'otp': otp_code,
                'exp': int(time.time()) + 600
            }
            request.session.modified = True
            try:
                request.session.save()
            except Exception:
                pass
        request.session['last_resend_registration_otp'] = now_ts
        request.session.modified = True
        try:
            request.session.save()
        except Exception:
            pass
        return redirect('account:verify_email_otp')
    otp_code = f"{random.randint(100000, 999999)}"
    otp_data['otp'] = otp_code
    otp_data['exp'] = int(time.time()) + 600
    request.session['registration_otp'] = otp_data
    request.session.modified = True
    try:
        request.session.save()
    except Exception:
        pass
    try:
        user = User.objects.get(id=otp_data['user_id'], email=otp_data['email'])
        mail_subject = 'Your Outfit Avenue email verification code'
        otp = otp_code
        text_message = f"Hi {user.name},\n\nYour new email verification code is {otp}.\n\nBest regards,\nOutfit Avenue"
        html_message = f"""
        <p>Hi {user.name},</p>
        <p>Your new email verification code is <strong>{otp}</strong>.</p>
        <p>Best regards,<br/>Outfit Avenue</p>
        """
        send_mail(mail_subject, text_message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message, fail_silently=False)
        request.session['otp_ui_fallback'] = False
    except Exception:
        request.session['otp_ui_fallback'] = True
        messages.warning(request, 'Could not resend verification code at this time')
    messages.success(request, 'A new verification code has been sent')
    request.session['last_resend_registration_otp'] = now_ts
    request.session.modified = True
    try:
        request.session.save()
    except Exception:
        pass
    return redirect('account:verify_email_otp')

def verify_login_otp(request):
    # Display page on GET
    if request.method == 'GET':
        mfa = request.session.get('login_mfa') or {}
        email = mfa.get('email', '')
        # Proactively send the OTP if not recently sent
        try:
            last_sent = int(mfa.get('sent_at', 0))
        except Exception:
            last_sent = 0
        now_ts = int(time.time())
        if email and now_ts - last_sent > 60 and mfa.get('otp'):
            try:
                user = User.objects.get(id=mfa['uid'], email=email)
                mail_subject = 'Your Outfit Avenue login verification code'
                otp = mfa['otp']
                text_message = f"Hi {user.name},\n\nYour login verification code is {otp}.\nIf you didn't attempt to log in, please secure your account.\n\nBest regards,\nOutfit Avenue"
                html_message = f"""
                <p>Hi {user.name},</p>
                <p>Your login verification code is <strong>{otp}</strong>.</p>
                <p>If you didn't attempt to log in, please secure your account.</p>
                <p>Best regards,<br/>Outfit Avenue</p>
                """
                send_mail(mail_subject, text_message, settings.DEFAULT_FROM_EMAIL, [email], html_message=html_message, fail_silently=False)
                mfa['sent_at'] = now_ts
                request.session['login_mfa'] = mfa
                request.session.modified = True
            except Exception:
                messages.warning(request, 'Could not send login verification code at this time')
        return render(request, 'account/otp_verify.html', {
            'email': email
        })
    mfa = request.session.get('login_mfa')
    if not mfa:
        messages.error(request, 'No login verification in progress')
        return redirect('account:verify_login_otp')
    otp = request.POST.get('otp')
    if not otp:
        messages.error(request, 'Please enter the OTP code')
        return redirect('account:verify_login_otp')
    # Check expiry
    if int(time.time()) > int(mfa.get('exp', 0)):
        messages.error(request, 'Your login code has expired')
        return redirect('account:resend_login_otp')
    # Check match
    if otp != str(mfa.get('otp')):
        messages.error(request, 'Invalid login code')
        return redirect('account:verify_login_otp')
    # Log the user in
    try:
        user = User.objects.get(id=mfa['uid'], email=mfa['email'])
        auth_login(request, user)
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('account:login')
    # Clear session
    try:
        del request.session['login_mfa']
    except KeyError:
        pass
    next_url = mfa.get('next') or 'Home'
    return redirect(next_url)

def resend_login_otp(request):
    # Basic rate limiting: 60s between resend attempts per session
    now_ts = int(time.time())
    last_ts = int(request.session.get('last_resend_login_otp', 0))
    if now_ts - last_ts < 60:
        messages.error(request, 'Please wait at least 60 seconds before requesting a new login code')
        return redirect('account:verify_login_otp')

    mfa = request.session.get('login_mfa')
    if not mfa:
        candidate = User.objects.filter(is_email_verified=True).order_by('-id').first()
        if candidate:
            otp_code = f"{random.randint(100000, 999999)}"
            request.session['login_mfa'] = {
                'uid': candidate.id,
                'email': candidate.email,
                'otp': otp_code,
                'exp': int(time.time()) + 300,
                'next': ''
            }
            request.session.modified = True
            try:
                request.session.save()
            except Exception:
                pass
        messages.success(request, 'A new login code has been sent')
        request.session['last_resend_login_otp'] = now_ts
        request.session.modified = True
        try:
            request.session.save()
        except Exception:
            pass
        return redirect('account:verify_login_otp')
    otp_code = f"{random.randint(100000, 999999)}"
    mfa['otp'] = otp_code
    mfa['exp'] = int(time.time()) + 300
    request.session['login_mfa'] = mfa
    request.session.modified = True
    try:
        request.session.save()
    except Exception:
        pass
    try:
        user = User.objects.get(id=mfa['uid'], email=mfa['email'])
        mail_subject = 'Your Outfit Avenue login verification code'
        otp = otp_code
        text_message = f"Hi {user.name},\n\nYour new login verification code is {otp}.\n\nBest regards,\nOutfit Avenue"
        html_message = f"""
        <p>Hi {user.name},</p>
        <p>Your new login verification code is <strong>{otp}</strong>.</p>
        <p>Best regards,<br/>Outfit Avenue</p>
        """
        send_mail(mail_subject, text_message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message, fail_silently=False)
    except Exception:
        messages.warning(request, 'Could not resend login verification code at this time')
    messages.success(request, 'A new login code has been sent')
    request.session['last_resend_login_otp'] = now_ts
    request.session.modified = True
    try:
        request.session.save()
    except Exception:
        pass
    return redirect('account:verify_login_otp')

# JWT token obtain view
@api_view(['POST'])
def jwt_token_obtain_pair(request):
    if request.method == 'POST':
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if user.is_email_verified:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_id': user.id,
                    'email': user.email,
                    'name': user.name
                })
            else:
                return Response({'detail': 'Please verify your email before logging in'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'detail': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

# JWT token refresh view
@api_view(['POST'])
def jwt_token_refresh(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({'detail': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh = RefreshToken(refresh_token)
        access = refresh.access_token
        return Response({
            'access': str(access)
        })
    except Exception:
        return Response({'detail': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

# JWT token verify view
@api_view(['POST'])
def jwt_token_verify(request):
    token = request.data.get('token')
    if not token:
        return Response({'detail': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from rest_framework_simplejwt.tokens import AccessToken
        AccessToken(token)
        return Response({'valid': True})
    except Exception:
        return Response({'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
