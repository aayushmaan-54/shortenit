# Auth Design
- Auth design for secure, stateless authentication using custom JWT
- Covers token storage, rotation, session handling and common attack prevention

## Tokens
- **Access token (AT)**
  - Short lived (~10-15 min)
  - Stored in client memory (JS variable), not `localStorage` / `sessionStorage`
  - Any script running on the page (XSS) can read `localStorage`; memory is harder to reach and is wiped on reload
  - Sent in `Authorization: Bearer <AT>` header
- **Refresh token (RT)**
  - Long lived (~7 days)
  - Stored in `HttpOnly; Secure; SameSite=Strict` cookie, `Path=/auth` (so both `/auth/refresh` and `/auth/logout` get it)
  - JS can't read it, browser attaches it automatically, and all tabs share the same cookie
- **Claims**
  - `sub` user id, `jti` unique token id, `iat`, `exp`
  - `iss` (our API) and `aud` (our frontend), validate both on decode
  - `type`: `access` | `refresh` (reject an RT used as an AT and vice versa)
  - `fid`: `family_id` (refresh token only)
  - `fgp`: fingerprint hash (see [Fingerprinting](#contextual-fingerprinting))
- Since AT lives in memory, every page reload / new tab calls `/refresh` first to get an AT
- **Decoding**
  - Pin the allowed algorithm (never trust the token's `alg` header)
  - Allow small clock skew leeway (~30s) for `exp` / `iat`

## Signing Keys
- HS256 with a strong random secret is fine for a single backend
- Switch to RS256 if other services need to verify tokens (they get only the public key)
- Add `kid` (key id) in JWT header so keys can be rotated without logging everyone out
  - New tokens signed with new key, old key kept for verification until its tokens expire

## Sessions (Source of Truth)
- **DB `sessions` table** is the source of truth: `family_id`, `user_id`, `current_jti`, `created_at`, `last_used_at`, device info
- **Redis** is the fast cache for `/refresh` checks
  - Redis miss -> fall back to DB, re-populate Redis
  - Redis restart doesn't log everyone out
- Revoke = delete from both (DB first, then Redis)
- Bonus: `sessions` table gives a "logged in devices" list + "logout from all devices" later

## Refresh Token Rotation
- On every `/refresh`:
  - Verify RT (signature, `exp`, `type`, `iss`, `aud`)
  - Check `jti` matches current one for its family
  - Check family is under its absolute lifetime (see below)
  - Invalidate old RT
  - Send new AT + new RT
  - Update `family:<family_id> -> jti` (Redis + DB)
- Do the check + update atomically (Lua script / `WATCH` + `MULTI`) so 2 parallel requests can't both pass
- **Absolute session lifetime**
  - Each rotation gives a new RT, so without a cap an active user stays logged in forever
  - Store `family_created_at`; if `now - family_created_at > 30 days` -> reject, force re-login
  - Redis key TTL = `min(rt_ttl, remaining absolute lifetime)`

## Reuse Detection
- On login create a new `family_id`; it identifies the whole session until RT expires
- Only the **latest** `jti` of a family is valid; anything older is a reused token
- Ex:
  - Attacker steals RT1, calls `/refresh` -> gets AT2 + RT2; current: `family:<id> -> RT2`
  - User later calls `/refresh` with RT1 -> `RT1 != RT2` -> **reuse detected**
  - Works the other way too: if user refreshes first, attacker's RT1 is now stale
- On reuse:
  - Revoke the whole family (DB session row + Redis key)
  - Optionally revoke all families of `sub` for stricter security
  - Both attacker and user are logged out; user logs in again
- Note: ATs already issued stay valid until they expire (no denylist), so keep AT TTL short

## Revoking All Sessions of a User
- `family:<id>` keys alone can't tell which families belong to a user
- Keep index: Redis set `user_families:<sub>` (add on login, remove on revoke) or query `sessions` table by `user_id`
- Used on: password change, ban / suspend, reuse detection (strict mode), "logout all devices"

## Multi-tab Race Condition
- Multiple tabs can call `/refresh` at the same time with the same RT
- 1st one rotates, 2nd one sends the now old RT -> **false reuse detection**
- Axios interceptor (single shared refresh promise + queue of failed requests) only fixes this inside **one tab**
- Fix in 2 layers: **Client** (avoid parallel refresh) + **Server** (grace period as safety net)

### Client: Web Locks + BroadcastChannel
- `BroadcastChannel` alone can't do this, it's just messaging, not a lock
  - 2 tabs can both send "I'm refreshing" at the same time and both refresh
  - A tab can't pause/queue requests of another tab
- Use **Web Locks API** (`navigator.locks.request("refresh", ...)`) for cross-tab mutual exclusion
- Flow:
  - Tab gets 401 (or AT about to expire) -> requests lock `refresh`
  - Only 1 tab holds the lock at a time; others wait
  - Lock holder: checks if a newer AT was already received via broadcast -> if yes, use it and skip
  - Else calls `/refresh`, saves new AT, broadcasts **only the AT** on `BroadcastChannel("auth")`, releases lock
  - Waiting tabs receive the AT (or get the lock, see fresh AT, skip refresh)
  - Inside each tab, Axios queue retries its failed requests with the new AT
- Broadcast only AT: RT is in an `HttpOnly` cookie, JS can't read it and every tab already has the new one
- **Tab closed mid-refresh**:
  - Browser auto releases the lock when the tab closes, the next waiting tab takes it -> no stuck queue
  - Still add a timeout (~10s) on waiting; on timeout, retry refresh yourself (server grace period covers it)

### Server: Grace Period
- Instead of instantly treating an old RT as stolen, allow it for a short window (~10s)
- In that window return the **same** already generated token pair, don't rotate again
- Need to store the new pair since it can't be regenerated identically
- Redis on rotation (RT1 -> RT2):
  - `SET family:<id> <RT2_jti> EX <ttl>`
  - `SET grace:<RT1_jti> <AT2 + RT2> EX 10` (use `EX` in the same command, not a separate `EXPIRE`)
- On `/refresh` with old RT:
  - `grace:<jti>` exists **and** family's current `jti` is still RT2 **and** fingerprint cookie matches -> return stored pair
  - else -> reuse detected
- Fingerprint check stops an attacker on another device from using the grace window
- Trade-offs:
  - Attacker inside the same window + same browser still gets the pair, keep the window small
  - Stored pair sits in plain text in Redis for 10s (acceptable; encrypt if Redis is shared)
  - Lost response edge case: server rotates, response drops (mobile network), client retries after 10s -> false reuse -> user logged out; rare, acceptable

## Logout
- Call `/auth/logout`: delete DB session row + `family:<id>` in Redis + remove from `user_families:<sub>`, clear RT + fgp cookies
- Broadcast `logout` on `BroadcastChannel("auth")` -> other tabs clear AT from memory and redirect to login
- Only syncs tabs of same browser; other devices log out when their AT expires and `/refresh` fails

## Token Revocation & Denylists (Will not use this)
- On logout, password change, ban or suspend, the AT stays valid until it expires
- Denylist fixes this gap:
  - Add AT `jti` to Redis denylist with TTL = AT remaining life
  - On every req check denylist, if present -> unauthorized
- But it adds a Redis lookup on every req and kills the main JWT benefit (stateless, zero latency validation); usually used for high security apps like banking
- Instead:
  - Keep AT TTL short
  - On password change / ban: revoke all RT families of the user -> no new ATs
- **Accepted trade-off**: banned user keeps access for up to AT TTL (~15 min); fine for most apps

## Contextual Fingerprinting
- Goal: a stolen AT should be useless outside the browser it was issued to
- **IP**: not usable, changes on mobile when network changes (WiFi <-> mobile data)
- **User-Agent hash**: weak, easy to spoof and changes on browser updates; don't rely on it
- **Fingerprint cookie** (use this):
  - On login / refresh server generates a random value (`secrets.token_hex(32)`)
  - Raw value -> cookie `__Secure-Fgp` (`HttpOnly; Secure; SameSite=Strict; Path=/`), sent on every API req
  - `SHA256(value)` -> `fgp` claim in AT (store the hash, never the raw value in the token)
  - On every req browser sends the cookie + AT header
  - Server hashes cookie value and compares with `fgp` claim using constant time compare (`hmac.compare_digest`, not `==`)
  - Attacker who steals the AT can't read the `HttpOnly` cookie, so can't use the AT on another machine
- RT is already in an `HttpOnly` cookie, so this mainly protects the AT; can also add `fgp` to RT and rotate it along with RT
