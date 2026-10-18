"""FastAPI dependencies for authentication.

`get_current_user` is the gatekeeper every protected endpoint uses:

    @router.get("/tasks")
    def list_tasks(current_user: User = Depends(get_current_user), ...)

How it works:
1. `OAuth2PasswordBearer` reads the `Authorization: Bearer <token>` header.
   If the header is missing/malformed it 401s automatically — we don't
   write that check ourselves.
2. We decode the token to a user id. A bad/expired token -> 401 with a
   `WWW-Authenticate: Bearer` header (the OAuth2 spec requires this header
   on 401s so clients know *how* to authenticate).
3. We load the user from the DB. If the user was deleted after the token
   was minted, the token is effectively dead -> 401.

Why a dependency and not copy-pasted code? Every protected route needs
exactly this logic. One function = one place to fix bugs, one place the
teaching happens.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

# tokenUrl must match the login route path — it's what the /docs "Authorize"
# button uses to fetch a token. It doesn't affect runtime behavior.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception
    # Tokens store the id as str (JWT claims must be JSON); the PK is int.
    user = db.get(User, int(user_id))
    if user is None:
        raise credentials_exception
    return user
