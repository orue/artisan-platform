"""JWT validation middleware for FastAPI.

Validates JWTs issued by Keycloak and extracts user identity.
Used as a FastAPI dependency in protected routes:

    from artisan_common.auth import get_current_user, User

    @router.get("/artworks")
    async def list_artworks(user: User = Depends(get_current_user)):
        print(f"Request from {user.sub} with roles {user.roles}")
"""

from dataclasses import dataclass, field
from typing import Any

import httpx
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

logger = structlog.get_logger()

# FastAPI security scheme — extracts Bearer token from Authorization header
_bearer_scheme = HTTPBearer()

# Cache for Keycloak's JWKS (JSON Web Key Set)
_jwks_cache: dict[str, Any] = {}


@dataclass(frozen=True)
class User:
    """Authenticated user extracted from a JWT."""

    sub: str  # Subject (unique user ID from Keycloak)
    email: str = ""
    name: str = ""
    roles: list[str] = field(default_factory=list)


async def _get_jwks(keycloak_url: str, realm: str) -> dict[str, Any]:
    """Fetch Keycloak's public keys for JWT verification.

    Keys are cached after first fetch. In production, you'd add
    TTL-based cache invalidation for key rotation.
    """
    if not _jwks_cache:
        jwks_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs"
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            _jwks_cache.update(response.json())
            logger.info("jwks_fetched", url=jwks_url)
    return _jwks_cache


def _extract_roles(claims: dict[str, Any]) -> list[str]:
    """Extract realm and client roles from Keycloak JWT claims."""
    roles: list[str] = []

    # Realm roles
    realm_access = claims.get("realm_access", {})
    roles.extend(realm_access.get("roles", []))

    # Client roles (from resource_access)
    resource_access = claims.get("resource_access", {})
    for _client, access in resource_access.items():
        roles.extend(access.get("roles", []))

    return roles


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    keycloak_url: str = "http://localhost:8080",
    realm: str = "artisan",
    audience: str = "artisan-api",
) -> User:
    """FastAPI dependency that validates JWT and returns the authenticated user.

    Raises HTTPException 401 if the token is missing, expired, or invalid.
    """
    token = credentials.credentials

    try:
        jwks = await _get_jwks(keycloak_url, realm)
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=audience,
            options={"verify_exp": True},
        )

        return User(
            sub=payload.get("sub", ""),
            email=payload.get("email", ""),
            name=payload.get("preferred_username", ""),
            roles=_extract_roles(payload),
        )

    except JWTError as e:
        logger.warning("jwt_validation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
