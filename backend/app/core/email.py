"""Email utility for sending password reset and notification emails."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
    
    @property
    def is_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and authenticate SMTP connection."""
        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        server.starttls()
        server.login(self.smtp_user, self.smtp_password)
        return server
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body content
            text_content: Optional plain text body (fallback)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning("SMTP not configured - email not sent")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email
            
            # Add plain text version if provided
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            
            # Add HTML version
            msg.attach(MIMEText(html_content, "html"))
            
            with self._create_smtp_connection() as server:
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return False


# Global email service instance
email_service = EmailService()


def send_password_reset_email(to_email: str, reset_url: str, username: str) -> bool:
    """
    Send password reset email.
    
    Args:
        to_email: User's email address
        reset_url: Password reset URL with token
        username: User's username for personalization
        
    Returns:
        True if email sent successfully, False otherwise
    """
    subject = "PEARL - Password Reset Request"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 28px;">PEARL</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">Password Reset Request</p>
        </div>
        
        <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
            <p>Hello <strong>{username}</strong>,</p>
            
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Reset Password</a>
            </div>
            
            <p style="color: #666; font-size: 14px;">Or copy and paste this link into your browser:</p>
            <p style="background: #f5f5f5; padding: 12px; border-radius: 4px; word-break: break-all; font-size: 13px; color: #555;">{reset_url}</p>
            
            <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 25px 0;">
            
            <p style="color: #888; font-size: 13px;">
                <strong>Note:</strong> This link will expire in 1 hour. If you didn't request a password reset, you can safely ignore this email.
            </p>
        </div>
        
        <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
            &copy; PEARL - Clinical Trials Tracker
        </p>
    </body>
    </html>
    """
    
    text_content = f"""
    PEARL - Password Reset Request
    
    Hello {username},
    
    We received a request to reset your password. Visit the link below to create a new password:
    
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request a password reset, you can safely ignore this email.
    
    - PEARL Team
    """
    
    return email_service.send_email(to_email, subject, html_content, text_content)


# =============================================================================
# Billing Email Functions
# =============================================================================

def send_welcome_email(to_email: str, tenant_name: str, login_url: str) -> bool:
    """
    Send welcome email to new tenant admin after signup.
    
    Args:
        to_email: Admin's email address
        tenant_name: Organization/tenant name
        login_url: URL to login page
        
    Returns:
        True if email sent successfully, False otherwise
    """
    subject = f"Welcome to PEARL - {tenant_name}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to PEARL!</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">{tenant_name}</p>
        </div>
        
        <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
            <p>Congratulations! Your PEARL account has been created successfully.</p>
            
            <p>Your 30-day free trial has started. Here's what you can do next:</p>
            
            <ul style="padding-left: 20px;">
                <li>Explore the sample data we've created for you</li>
                <li>Invite team members to collaborate</li>
                <li>Create your first study and reporting effort</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{login_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Get Started</a>
            </div>
            
            <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 25px 0;">
            
            <p style="color: #888; font-size: 13px;">
                Need help? Check out our <a href="{login_url.replace('/login', '/help')}" style="color: #667eea;">help center</a> or reply to this email.
            </p>
        </div>
        
        <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
            &copy; PEARL - Package, Effort and Analysis Reporting Library
        </p>
    </body>
    </html>
    """
    
    text_content = f"""
    Welcome to PEARL!
    
    {tenant_name}
    
    Congratulations! Your PEARL account has been created successfully.
    
    Your 30-day free trial has started. Here's what you can do next:
    
    - Explore the sample data we've created for you
    - Invite team members to collaborate
    - Create your first study and reporting effort
    
    Get started: {login_url}
    
    Need help? Visit our help center or reply to this email.
    
    - PEARL Team
    """
    
    return email_service.send_email(to_email, subject, html_content, text_content)


def send_trial_ending_email(to_email: str, tenant_name: str, days_remaining: int, billing_url: str) -> bool:
    """
    Send reminder that trial is ending soon.
    
    Args:
        to_email: Admin's email address
        tenant_name: Organization name
        days_remaining: Days left in trial
        billing_url: URL to billing page
        
    Returns:
        True if email sent successfully
    """
    subject = f"PEARL - Your trial ends in {days_remaining} days"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 30px; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 28px;">Trial Ending Soon</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">{days_remaining} days remaining</p>
        </div>
        
        <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
            <p>Hi there,</p>
            
            <p>Your free trial for <strong>{tenant_name}</strong> will end in <strong>{days_remaining} days</strong>.</p>
            
            <p>To continue using PEARL without interruption, please add your payment method:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{billing_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Manage Subscription</a>
            </div>
            
            <p style="color: #666; font-size: 14px;">
                Don't worry - you won't be charged until your trial ends, and you can cancel anytime.
            </p>
        </div>
        
        <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
            &copy; PEARL - Package, Effort and Analysis Reporting Library
        </p>
    </body>
    </html>
    """
    
    text_content = f"""
    Trial Ending Soon - {days_remaining} days remaining
    
    Hi there,
    
    Your free trial for {tenant_name} will end in {days_remaining} days.
    
    To continue using PEARL without interruption, please add your payment method:
    
    {billing_url}
    
    Don't worry - you won't be charged until your trial ends, and you can cancel anytime.
    
    - PEARL Team
    """
    
    return email_service.send_email(to_email, subject, html_content, text_content)


def send_payment_failed_email(to_email: str, tenant_name: str, grace_days: int, billing_url: str) -> bool:
    """
    Send notification that payment has failed.
    
    Args:
        to_email: Admin's email address
        tenant_name: Organization name
        grace_days: Days of grace period remaining
        billing_url: URL to update payment
        
    Returns:
        True if email sent successfully
    """
    subject = "PEARL - Payment Failed - Action Required"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 30px; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 28px;">Payment Failed</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">Action required</p>
        </div>
        
        <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
            <p>Hi there,</p>
            
            <p>We were unable to process the payment for <strong>{tenant_name}</strong>.</p>
            
            <p style="background: #fef2f2; border: 1px solid #fecaca; padding: 15px; border-radius: 6px; color: #991b1b;">
                <strong>Important:</strong> Please update your payment method within <strong>{grace_days} days</strong> to avoid service interruption.
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{billing_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Update Payment Method</a>
            </div>
            
            <p style="color: #666; font-size: 14px;">
                If you believe this is an error, please check with your bank or contact our support team.
            </p>
        </div>
        
        <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
            &copy; PEARL - Package, Effort and Analysis Reporting Library
        </p>
    </body>
    </html>
    """
    
    text_content = f"""
    Payment Failed - Action Required
    
    Hi there,
    
    We were unable to process the payment for {tenant_name}.
    
    IMPORTANT: Please update your payment method within {grace_days} days to avoid service interruption.
    
    Update payment: {billing_url}
    
    If you believe this is an error, please check with your bank or contact our support team.
    
    - PEARL Team
    """
    
    return email_service.send_email(to_email, subject, html_content, text_content)


def send_subscription_canceled_email(to_email: str, tenant_name: str, reactivate_url: str) -> bool:
    """
    Send confirmation that subscription has been canceled.
    
    Args:
        to_email: Admin's email address
        tenant_name: Organization name
        reactivate_url: URL to reactivate subscription
        
    Returns:
        True if email sent successfully
    """
    subject = "PEARL - Subscription Canceled"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); padding: 30px; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 28px;">Subscription Canceled</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">{tenant_name}</p>
        </div>
        
        <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
            <p>Hi there,</p>
            
            <p>Your PEARL subscription for <strong>{tenant_name}</strong> has been canceled.</p>
            
            <p>Your data will be retained for 90 days. During this time, you can reactivate your subscription to regain full access.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reactivate_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Reactivate Subscription</a>
            </div>
            
            <p style="color: #666; font-size: 14px;">
                We're sorry to see you go. If you have any feedback about how we can improve PEARL, we'd love to hear from you.
            </p>
        </div>
        
        <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
            &copy; PEARL - Package, Effort and Analysis Reporting Library
        </p>
    </body>
    </html>
    """
    
    text_content = f"""
    Subscription Canceled
    
    Hi there,
    
    Your PEARL subscription for {tenant_name} has been canceled.
    
    Your data will be retained for 90 days. During this time, you can reactivate your subscription to regain full access.
    
    Reactivate: {reactivate_url}
    
    We're sorry to see you go. If you have any feedback, we'd love to hear from you.
    
    - PEARL Team
    """
    
    return email_service.send_email(to_email, subject, html_content, text_content)



