# TrustRent

A property rental and sales platform for Ghana, built around one question: **can you prove the person showing you a house actually owns it?**

Django REST backend · React frontend · PostgreSQL · JWT auth

> **Status: backend complete and tested, frontend partial, blockchain ledger not started.**
> This was my final-year capstone at Ashesi University. The section [What's built and what isn't](#whats-built-and-what-isnt) is precise about where the line falls — nothing below is aspirational.

---

## Why this exists

My mother was scammed renting a house. We were moving in a hurry and I wasn't there. A man showed her the property — he had keys, he had answers — she paid, and he left. She had the gate key. She never had the house key. He was not the owner, and the money was gone.

What struck me afterwards was how little would have prevented it. Not better judgement, not more caution — just a way to check, in the moment she was standing at that gate, whether the man holding the keys was the registered owner.

So I looked into how property ownership is actually verified in Ghana. Two bodies hold that authority: the **Lands Commission** (ownership and title) and **Rent Control** (tenancy terms and disputes). Neither is reachable at the speed a rental decision gets made. The verification exists — it's just not available to the person who needs it, at the moment they need it.

TrustRent is an attempt to put it there.

## How it verifies

Ownership claims are not self-asserted. The flow deliberately puts a human authority in the middle:

1. An owner registers and uploads a government ID. They cannot list anything until an admin verifies them.
2. A verified owner registers a property and uploads its **title deed**.
3. A **Lands Commission representative** — a distinct role in the system — reviews the deed and approves or rejects the claim.
4. Only then can the property be listed.
5. A seeker browsing listings sees verification status, and can request access to the supporting documents. The owner approves or denies each request.

Title deeds are not public. `DocumentAccessRequest` exists so a seeker can ask to see proof and the owner can consent — rather than either publishing private documents or asking people to trust a badge.

The four roles — `property_owner`, `property_seeker`, `land_commission_rep`, `sys_admin` — come straight from that research. The Lands Commission representative is in the data model because the real-world verification path runs through them.

---

## What's built and what isn't

| Component | Status | Detail |
|---|---|---|
| User management | ✅ Complete | Registration, JWT auth, RBAC, admin verification of users |
| Property management | ✅ Complete | Creation, deed and image upload, Lands Commission verification |
| Document access control | ✅ Complete | Request / approve / deny flow for private documents |
| Listings | ✅ Complete | Create, browse, detail, deactivate, reactivate |
| Test suite | ✅ 43 tests | ~1,180 lines across 5 files |
| Frontend | ⚠️ Partial | 5 pages against 20 endpoints — auth and owner flows only |
| Blockchain ledger | ❌ Not started | `ledger` app is an empty Django stub |

### On the blockchain

The original design called for property ownership to be recorded on a blockchain, so that a chain of transfers would be visible and immutable, with smart contracts handling ownership transfer and rental agreements.

**None of that is implemented.** The `ledger` app exists as an empty Django app with its own database configured and routed, and that is the extent of it.

Leaving the scaffolding in place was deliberate — the three-database split (below) was designed around it. But a stub is a stub, and the repository would be misleading if it implied otherwise.

I'd also now question part of the original premise. A blockchain makes a record tamper-evident; it does not make the record *true*. If a fraudulent ownership claim is written to the chain, the chain faithfully preserves a lie. The part of this system that actually prevents my mother's scam is the Lands Commission verification step — the human authority checking a deed — and that part is built. The ledger would add auditability of transfers on top of verified data, which is worth having, but it is not the thing doing the work.

---

## Architecture

```
React (frontend/)
      │  JWT
      ▼
Django REST Framework
      │
      ├── core    ──► trustrent_core_db     users, properties, documents, verification
      ├── ops     ──► trustrent_ops_db      listings, agreements, reviews
      └── ledger  ──► trustrent_ledger_db   (stub — reserved for the chain)
                │
         TrustRentRouter
```

### Three databases, one router

Each Django app owns a separate PostgreSQL database, wired up by a custom router in [`TrustRent/db_router.py`](TrustRent/db_router.py). `allow_migrate` pins each app's tables to its own database and returns `False` by default, so a stray migration can't write across the boundary.

The reason is the ledger. Append-only ownership records have different durability and access requirements from ordinary application data, and separating them at the database level meant the ledger could later be replaced — by a real chain, or by a database with different guarantees — without touching `core` or `ops`.

The honest cost: cross-database foreign keys don't work in Django. `allow_relation` permits relations where one side is `core`, and the models reference across databases by ID rather than by a real constraint. That trade is why `core` holds anything referenced from elsewhere.

### Data model

**core** — `User`, `Property`, `PropertyImage`, `UserProperty`, `PropertyDocument`, `VerificationHistory`, `DocumentAccessRequest`

**ops** — `PropertyListing`, `PropertyReviewRequest`, `PurchaseAgreement`, `RentalReview`

`UserProperty` is the ownership link, carrying the verification state — a property is not owned in the system until that record is approved.

### API

20 endpoints across `core` and `ops`:

```
POST  user/register/                  POST  property/create/
POST  user/login/                     POST  property/upload-document/
GET   user/unverified/                POST  property/upload-image/
POST  user/verify/                    GET   property/unverified/
                                      POST  property/verify/
POST  document/request-access/        POST  property/reject/
POST  document/respond/               GET   property/all/
GET   document/requests/              GET   property/<id>/

POST  listing/create/                 GET   listings/
GET   listing/<id>/                   POST  listing/<id>/deactivate/
                                      POST  listing/<id>/reactivate/
```

Postman collections for manual testing are in [`postman_collections/`](postman_collections/).

---

## Running it

Requires Python 3.10+, PostgreSQL 14+, Node 18+.

```bash
git clone https://github.com/Princess09-best/TrustRent.git
cd TrustRent
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create the three databases:

```sql
CREATE DATABASE trustrent_core_db;
CREATE DATABASE trustrent_ops_db;
CREATE DATABASE trustrent_ledger_db;
```

Configure secrets — copy the template and fill in your own values:

```bash
cp .env.example .env
```

`.env` is gitignored and must never be committed. Generate a fresh `DJANGO_SECRET_KEY` with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Then migrate each database and run:

```bash
python manage.py migrate --database=default
python manage.py migrate --database=core
python manage.py migrate --database=ops
python manage.py migrate --database=ledger
python manage.py runserver
```

Frontend:

```bash
cd frontend && npm install && npm start
```

### Tests

```bash
python manage.py test
```

43 tests covering registration and authentication, RBAC, admin user verification, property creation, deed and image upload, Lands Commission verification, document access requests, and the listing lifecycle.

---

## What I'd do next

1. **Finish the frontend.** The backend exposes 20 endpoints; the UI reaches five of them. Seeker-side browsing and the document request flow are the gaps that matter most, since they're what an actual renter would use.
2. **Build the ledger** — an append-only transfer record first, before any distributed chain. Most of the value is in the audit trail, and that doesn't require a blockchain.
3. **Replace the hand-rolled auth on `User`.** I store a `password_hash` on a plain model rather than extending Django's auth user, which means re-implementing things Django already does correctly. That was a mistake and I'd fix it before adding features.
4. **Real Lands Commission integration.** Currently a human representative reviews deeds inside the app. An API — if one is ever exposed — would close the loop.

---

## A note on this repository's history

An earlier version of `settings.py` committed a database password and the Django `SECRET_KEY` in plaintext. Both have been moved to environment variables, and the exposed credentials have been rotated.

They remain visible in the git history, which is why rotation rather than deletion is the fix. Leaving this note here rather than quietly removing it: it was a real mistake, and the lesson — secrets belong in the environment, and a leaked secret must be changed, not just hidden — was worth learning early.

---

Built by [Princess Asiru-Balogun](https://github.com/Princess09-best) · Ashesi University capstone, 2025
