"""OAuth2/OIDC integration using authlib."""

from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

from app.core.config import settings


# Initialize OAuth registry
oauth = OAuth()


# Google OAuth2 Configuration
if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name='google',
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )


# Microsoft/Azure AD OAuth2 Configuration
if settings.microsoft_client_id and settings.microsoft_client_secret:
    oauth.register(
        name='microsoft',
        client_id=settings.microsoft_client_id,
        client_secret=settings.microsoft_client_secret,
        server_metadata_url=f'https://login.microsoftonline.com/{settings.microsoft_tenant_id}/v2.0/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )


# GitHub OAuth2 Configuration
if settings.github_client_id and settings.github_client_secret:
    oauth.register(
        name='github',
        client_id=settings.github_client_id,
        client_secret=settings.github_client_secret,
        authorize_url='https://github.com/login/oauth/authorize',
        authorize_params=None,
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_params=None,
        client_kwargs={'scope': 'user:email'},
    )


def get_oauth_client(provider: str):
    """
    Get OAuth client for a specific provider.
    
    Args:
        provider: OAuth provider name (google, microsoft, github)
    
    Returns:
        OAuth client instance
    
    Raises:
        ValueError: If provider is not configured
    """
    if not hasattr(oauth, provider):
        raise ValueError(f"OAuth provider '{provider}' is not configured")
    
    return getattr(oauth, provider)


async def get_user_info_from_token(provider: str, token: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user information from OAuth token.
    
    Args:
        provider: OAuth provider name
        token: OAuth token response
    
    Returns:
        Dict containing user info (email, name, provider_id)
    """
    client = get_oauth_client(provider)
    
    if provider == 'google':
        # Google provides userinfo endpoint
        resp = await client.get('https://www.googleapis.com/oauth2/v1/userinfo', token=token)
        user_data = resp.json()
        return {
            'email': user_data.get('email'),
            'name': user_data.get('name'),
            'provider_id': user_data.get('id'),
            'picture': user_data.get('picture'),
        }
    
    elif provider == 'microsoft':
        # Microsoft provides userinfo endpoint
        resp = await client.get('https://graph.microsoft.com/v1.0/me', token=token)
        user_data = resp.json()
        return {
            'email': user_data.get('mail') or user_data.get('userPrincipalName'),
            'name': user_data.get('displayName'),
            'provider_id': user_data.get('id'),
        }
    
    elif provider == 'github':
        # GitHub requires separate email endpoint
        resp = await client.get('https://api.github.com/user', token=token)
        user_data = resp.json()
        
        # Get primary email
        email_resp = await client.get('https://api.github.com/user/emails', token=token)
        emails = email_resp.json()
        primary_email = next(
            (e['email'] for e in emails if e.get('primary')), 
            emails[0]['email'] if emails else None
        )
        
        return {
            'email': primary_email,
            'name': user_data.get('name') or user_data.get('login'),
            'provider_id': str(user_data.get('id')),
            'picture': user_data.get('avatar_url'),
        }
    
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def is_provider_configured(provider: str) -> bool:
    """Check if an OAuth provider is configured."""
    return hasattr(oauth, provider)

