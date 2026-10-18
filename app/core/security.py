"""Password hashing and JWT helpers.

Why bcrypt?
- It's deliberately SLOW (that's the point). A fast hash like SHA-256 lets
  an attacker try billions of passwords per second on stolen hashes; bcrypt
  is tunable so it stays slow even as hardware gets faster.
- It salts automatically: two users with the same password get different
  hashes, so rainbow tables are useless.

Why JWT (JSON Web Tokens) for auth?
- Stateless: the server doesn't store sessions. The token itself carries the
  user id ("sub" claim) plus an expiry, signed with SECRET_KEY. Any server
  instance can verify it without a DB lookup — this is what lets APIs scale
  horizontally.
- Trade-off: you can't easily revoke a single token before it expires
  (that's what short expiries + refresh tokens are for — out of scope here).
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# One context for the whole app: scheme choice lives in exactly one place,
# so upgrading the algorithm later is a one-line change.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Turn a plaintext password into a bcrypt hash for storage."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Check a login attempt against the stored hash (timing-safe)."""
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str) -> str:
    """Mint a signed JWT whose subject ("sub") is the user id.

    `subject` is a str because JWT claims must be JSON-serializable —
    we str() the int user id at the call site and int() it back when reading.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Return the user id from a token, or None if it's invalid/expired.

    Returns None instead of raising so the auth dependency can translate
    "bad token" into a clean 401 in one place.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None
