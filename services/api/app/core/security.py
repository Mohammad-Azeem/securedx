"""
SecureDx AI — Authentication & Authorization

RBAC Roles:
  - admin:              System administration, user management
  - physician:          Run inference, view results, submit overrides
  - compliance_officer: View audit logs, export reports (read-only)

Token validation uses Keycloak JWKS for signature verification.
Break-glass access is a special override for emergency scenarios.
"""

from enum import StrEnum
from functools import lru_cache
from typing import Annotated

import httpx
import structlog
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwk, jwt
from pydantic import BaseModel

from app.core.config import settings

logger = structlog.get_logger(__name__)

security = HTTPBearer(auto_error=True)


# =============================================================================
# ROLES
# =============================================================================

class Role(StrEnum):
    ADMIN = "admin"
    PHYSICIAN = "physician"
    COMPLIANCE_OFFICER = "compliance_officer"


# =============================================================================
# CURRENT USER MODEL
# =============================================================================

class CurrentUser(BaseModel):
    user_id: str                    # Keycloak subject (UUID)
    email: str
    full_name: str
    roles: list[Role]
    clinic_id: str
    is_active: bool = True
    is_break_glass: bool = False    # True during a break-glass session

    @property
    def role(self) -> str:
        """
        Backward-compatible primary role accessor used by older endpoints.
        """
        return self.roles[0].value if self.roles else ""


# =============================================================================
# JWKS KEY FETCHING (cached, auto-refreshes on 401)
# =============================================================================

_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    """Fetch Keycloak's JSON Web Key Set for token signature verification."""
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(settings.KEYCLOAK_JWKS_URL)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        return _jwks_cache


def _invalidate_jwks_cache():
    global _jwks_cache
    _jwks_cache = None


# =============================================================================
# TOKEN VALIDATION
# =============================================================================

async def _validate_token(token: str) -> dict:
    """
    Validate a Keycloak-issued JWT.
    Returns the decoded claims dict on success.
    Raises HTTP 401 on any validation failure.
    """
    try:
        jwks = await _get_jwks()

        # Decode header to find the right key
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find matching key in JWKS
        rsa_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if not rsa_key:
            _invalidate_jwks_cache()  # Force refresh on next call
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find signing key",
            )

        claims = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.KEYCLOAK_CLIENT_ID,
            options={"verify_exp": True},
        )
        return claims

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.warning("JWT validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _extract_roles(claims: dict) -> list[Role]:
    """Extract SecureDx roles from Keycloak realm_access claims."""
    realm_roles = claims.get("realm_access", {}).get("roles", [])
    valid_roles = set(r.value for r in Role)
    return [Role(r) for r in realm_roles if r in valid_roles]


# =============================================================================
# FASTAPI DEPENDENCIES
# =============================================================================

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)],
) -> CurrentUser:
    """
    FastAPI dependency: validates bearer token and returns current user.

    Usage:
        @router.get("/protected")
        async def endpoint(user: CurrentUser = Depends(get_current_user)):
            ...
    """
    claims = await _validate_token(credentials.credentials)

    roles = _extract_roles(claims)
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No SecureDx role assigned to this account",
        )

    # Verify clinic_id matches this node's clinic
    token_clinic = claims.get("clinic_id") or claims.get("clinic")
    if token_clinic and token_clinic != settings.CLINIC_ID:
        logger.warning(
            "Cross-clinic token attempt blocked",
            token_clinic=token_clinic,
            local_clinic=settings.CLINIC_ID,
            subject=claims.get("sub"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token is not valid for this clinic node",
        )

    return CurrentUser(
        user_id=claims["sub"],
        email=claims.get("email", ""),
        full_name=claims.get("name", claims.get("preferred_username", "")),
        roles=roles,
        clinic_id=settings.CLINIC_ID,
        is_active=not claims.get("disabled", False),
    )


def require_roles(*required_roles: Role):
    """
    Dependency factory: enforces that the current user has at least one
    of the specified roles.

    Usage:
        @router.post("/admin-only")
        async def endpoint(
            user: CurrentUser = Depends(require_roles(Role.ADMIN))
        ):
    """
    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        user_role_set = set(user.roles)
        if not user_role_set.intersection(set(required_roles)):
            logger.warning(
                "Access denied — insufficient role",
                user_id=user.user_id,
                user_roles=[r.value for r in user.roles],
                required_roles=[r.value for r in required_roles],
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access requires one of: {[r.value for r in required_roles]}",
            )
        return user

    return _check


# Convenience dependency aliases
require_physician = require_roles(Role.PHYSICIAN, Role.ADMIN)
require_admin = require_roles(Role.ADMIN)
require_compliance = require_roles(Role.COMPLIANCE_OFFICER, Role.ADMIN)
