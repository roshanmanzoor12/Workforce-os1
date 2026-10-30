import uuid

from app.modules.auth.tokens import (
    create_refresh_token_hash,
    create_token_pair,
    parse_access_token,
    parse_refresh_token,
)


user_id = uuid.uuid4()

pair = create_token_pair(
    user_id=user_id
)

print("USER:")
print(user_id)

print("\nSESSION:")
print(pair.session_id)

print("\nACCESS CLAIMS:")
access = parse_access_token(
    pair.access_token
)
print(access)

print("\nREFRESH CLAIMS:")
refresh = parse_refresh_token(
    pair.refresh_token
)
print(refresh)

print("\nREFRESH HASH:")
print(
    create_refresh_token_hash(
        pair.refresh_token
    )
)

print("\nCHECKS:")
print(
    "Access user matches:",
    access.user_id == user_id,
)

print(
    "Refresh user matches:",
    refresh.user_id == user_id,
)

print(
    "Same session:",
    access.session_id
    == refresh.session_id
    == pair.session_id,
)