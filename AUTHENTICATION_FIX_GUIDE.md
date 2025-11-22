# Authentication Fix Guide

## Issues Fixed

1. **Gmail Authentication Error**: Fixed email configuration and added console backend for development
2. **Better Error Handling**: Added user-friendly error messages for email failures
3. **Improved User Flow**: Unverified users can now resend verification OTPs during login
4. **Email Helper Function**: Centralized email sending with better error handling

## Quick Fix for Gmail Authentication

The error you're seeing (`BadCredentials`) means Gmail is rejecting your password. Here are the solutions:

### Option 1: Use Console Email Backend (Recommended for Development)

The system is now configured to use console email backend when `DEBUG=True`. This means emails will be printed to your terminal/console instead of being sent via SMTP. This is perfect for development and testing.

**No action needed** - it's already configured! Just run your server and check the console for OTP codes.

### Option 2: Use Gmail App Password (For Production)

If you want to use actual email sending, you need to create a Gmail App Password:

1. Go to your Google Account: https://myaccount.google.com/
2. Click on **Security** in the left sidebar
3. Enable **2-Step Verification** (if not already enabled)
4. Scroll down to **App passwords**
5. Click **Select app** → Choose "Mail"
6. Click **Select device** → Choose "Other" and type "Django"
7. Click **Generate**
8. Copy the 16-character password (it will look like: `abcd efgh ijkl mnop`)
9. Update `Ecommerceweb/settings.py`:
   ```python
   EMAIL_HOST_PASSWORD = 'your-16-character-app-password'  # Remove spaces
   ```

### Option 3: Use Environment Variables (Recommended for Production)

For better security, use environment variables:

1. Create a `.env` file in your project root (add it to `.gitignore`):
   ```
   EMAIL_HOST_USER=garmy564@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password-here
   USE_CONSOLE_EMAIL=False
   ```

2. Install python-decouple (optional but recommended):
   ```bash
   pip install python-decouple
   ```

3. Update `settings.py` to use environment variables (already configured)

## Running Tests

### Run All Authentication Tests

```bash
python manage.py test account.test_authentication
```

### Run Specific Test Classes

```bash
# Test registration only
python manage.py test account.test_authentication.RegistrationTestCase

# Test OTP verification only
python manage.py test account.test_authentication.OTPVerificationTestCase

# Test login only
python manage.py test account.test_authentication.LoginTestCase

# Test login OTP only
python manage.py test account.test_authentication.LoginOTPTestCase

# Test email sending
python manage.py test account.test_authentication.EmailSendingTestCase

# Test complete flow
python manage.py test account.test_authentication.IntegrationTestCase
```

### Run Original Tests

```bash
python manage.py test account.tests
```

### Run All Tests

```bash
python manage.py test account
```

## Test Cases Overview

### RegistrationTestCase
- ✅ Successful registration with OTP
- ✅ Missing required fields
- ✅ Password mismatch
- ✅ Duplicate email (verified user)
- ✅ Duplicate email (unverified user - resends OTP)

### OTPVerificationTestCase
- ✅ Successful OTP verification
- ✅ Invalid OTP
- ✅ Expired OTP
- ✅ Resend OTP

### LoginTestCase
- ✅ Login with verified user (sends login OTP)
- ✅ Login with unverified user (sends verification OTP)
- ✅ Invalid credentials
- ✅ Missing fields

### LoginOTPTestCase
- ✅ Successful login OTP verification
- ✅ Invalid login OTP
- ✅ Resend login OTP

### EmailSendingTestCase
- ✅ Email sent on registration

### IntegrationTestCase
- ✅ Complete registration flow (register → verify → login → login OTP)
- ✅ Unverified user login flow (login → verify email → login OTP)

## Manual Testing Checklist

### Registration Flow
1. [ ] Go to `/account/register/`
2. [ ] Fill in all required fields
3. [ ] Submit form
4. [ ] Check console/terminal for OTP code
5. [ ] Go to OTP verification page
6. [ ] Enter OTP code
7. [ ] Verify redirect to login page
8. [ ] Check user is verified in database

### Login Flow (Verified User)
1. [ ] Go to `/account/login/`
2. [ ] Enter email and password
3. [ ] Submit form
4. [ ] Check console/terminal for login OTP
5. [ ] Enter login OTP
6. [ ] Verify redirect to home page
7. [ ] Check user is logged in

### Login Flow (Unverified User)
1. [ ] Create unverified user
2. [ ] Go to `/account/login/`
3. [ ] Enter email and password
4. [ ] Submit form
5. [ ] Verify redirect to email verification page
6. [ ] Check console/terminal for verification OTP
7. [ ] Enter verification OTP
8. [ ] Verify redirect to login page
9. [ ] Login again with same credentials
10. [ ] Enter login OTP
11. [ ] Verify successful login

### Error Cases
1. [ ] Try registration with existing verified email → Should redirect to login
2. [ ] Try registration with existing unverified email → Should resend OTP
3. [ ] Try login with wrong password → Should show error
4. [ ] Try OTP verification with wrong OTP → Should show error
5. [ ] Try OTP verification with expired OTP → Should redirect to resend

## Troubleshooting

### Email Not Sending
- Check if `DEBUG=True` in settings (uses console backend)
- Check Gmail App Password is correct
- Check internet connection
- Check email settings in `settings.py`

### OTP Not Working
- Check session is enabled in settings
- Check OTP hasn't expired (10 minutes for registration, 5 minutes for login)
- Check you're using the correct OTP from console/email

### User Not Verified
- Check `is_email_verified` field in database
- Try resending OTP
- Check OTP verification was successful

## Configuration

### Current Email Settings

The system automatically uses console backend when `DEBUG=True`. To change:

```python
# In Ecommerceweb/settings.py
USE_CONSOLE_EMAIL = False  # Set to False to use SMTP
```

Or set environment variable:
```bash
export USE_CONSOLE_EMAIL=False
```

## Security Notes

1. **Never commit email passwords to git** - Use environment variables
2. **Use App Passwords** - Don't use your regular Gmail password
3. **Enable 2FA** - Required for App Passwords
4. **Rotate Passwords** - Change App Passwords regularly

## Next Steps

1. Test the registration flow
2. Test the login flow
3. Verify OTP codes appear in console
4. If needed, set up Gmail App Password for production
5. Run all test cases to ensure everything works

