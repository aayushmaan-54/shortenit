- fastapi[standard]
- pydantic
- pydantic-settings
- python-json-logger
- pytimeparse2
- redis
- limits
- pyjwt[crypto]
- pwdlib[argon2]
- cryptography

Run: uvicorn app.main:app --no-server-header

# Auth
- Custom JWT auth
- Refresh Token Rotation
- Reuse detection
- Multi-tab sync (Web Locks + BroadcastChannel)
- Contextual Fingerprinting
- For more see [Auth Design](docs/auth.md)
