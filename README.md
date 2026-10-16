# `ShortenIt`: Multi-Tenant URL Shortener & Analytics
A high-throughput, multi-tenant URL shortening service built to handle sub-millisecond redirects and real-time analytics at scale.

## Features
* **Auth & Profiles:** Email/Password, Confirm User, New device login detection, Multi device login support, Token revocation, Rotating refresh tokens + Reuse detection, Google OAuth, OTP-protected sensitive actions, and avatar uploads.
* **Multi-Tenancy & RBAC:** Organization workspaces with granular custom role creation (view/edit/delete permissions per entity).
* **URL Management:** Generate links (Random, Friendly, Custom Alias, Custom Domain). Edit, pause, share (QR/Web Share), and export data (CSV/Excel/PDF).
* **Real-Time Analytics:** Track total/unique views, geographic location, referrers, OS/Device, UTM parameters, and QR vs. direct clicks.
* **Monetization:** Stripe-integrated tiered pricing (Free, Silver, Gold) enforcing usage limits and feature gating.

## Tech Stack
* **Frontend:** React.js, Tailwind CSS, TanStack (Router, Query, Table, Charts)
* **Backend:** FastAPI (Python), Motor (Async Driver), JWT Auth
* **Databases:** MongoDB (OLTP), Redis (Cache & Message Broker), ClickHouse (OLAP Analytics)
* **Infrastructure:** Docker, Caddy (Reverse Proxy), AWS S3

## Architecture Decisions
* **Zero-Collision URL Generation:** A background worker pre-generates unique strings into a Redis list. The API performs an `O(1)` `LPOP` to grab a hash during link creation, preventing MongoDB race conditions.
* **Cache Stampede Protection:** On a Redis cache miss during a traffic spike, a Redis Mutex (`SETNX`) lock is applied. Only the first thread queries MongoDB to populate the cache; concurrent threads wait 50ms and read directly from Redis.
* **Event-Driven Analytics:** To ensure redirects remain sub-millisecond, the API never writes clicks to the database. Clicks are published to Redis Streams, where a background consumer batches and bulk-inserts them into ClickHouse.
* **Metadata CDC Pipeline:** MongoDB Change Streams sync relational data (Organizations, Users, URLs) to ClickHouse so analytical queries can JOIN against up-to-date metadata without touching the primary database.
* **Hybrid Cached RBAC:** User permissions are computed into bitmasks at login and stored in Redis/JWT, enabling zero-database authorization checks on every API request.
* **Custom Domain SSL:** Caddy is used as the edge proxy with On-Demand TLS enabled, allowing the system to dynamically generate Let's Encrypt certificates the first time a user visits a verified custom domain.
