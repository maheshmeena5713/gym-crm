PROJECT NAME: GymEdge

PROJECT TYPE:
AI-powered Gym Management SaaS (AI Wrapper + Automation Platform)

---

HIGH LEVEL VISION

GymEdge is a multi-tenant SaaS platform for gym owners.

It combines:
- Traditional gym management (members, plans, payments)
- AI-driven retention analytics
- AI workout generation
- AI diet generation
- WhatsApp automation
- Business intelligence dashboards

Positioning:
“AI Co-Pilot for Gym Owners”

The product helps gym owners:
- Reduce churn
- Increase renewals
- Automate operations
- Improve member engagement
- Track business health

---

TECH STACK

Backend:
- Django
- PostgreSQL
- Gunicorn
- Nginx

Infrastructure:
- 1GB VPS
- No Redis
- No Celery
- No background workers
- DB sessions only
- Keep infra extremely lightweight

Frontend:
- Django Templates
- Dark SaaS UI
- Dashboard-based layout

Deployment:
- Single server deployment
- Cron jobs allowed
- No distributed services

---

ARCHITECTURE STYLE

- Multi-tenant by gym
- All data isolated by gym_id
- Every model includes gym FK
- Gym selected via login using gym_code
- Plan-based feature restrictions (Starter, Growth, Pro)

---

PLANS

Starter:
- Up to 150 members
- Basic dashboard
- Member management

Growth:
- Up to 500 members
- Leads
- WhatsApp automation (basic)
- Analytics dashboard

Pro:
- Up to 5000 members
- AI workout generator
- AI diet generator
- Advanced analytics
- WhatsApp automation (advanced)
- Retention AI

Feature access is strictly controlled by plan.

---

CORE MODULES

1. Authentication
- Gym code based login
- Owner role
- Future: staff roles

2. Members
- Add member
- Edit member
- Plans (monthly, quarterly, yearly)
- Expiry tracking
- Status (active, expired, frozen)
- Fitness profile

3. Leads
- Lead pipeline
- AI scoring
- Conversion tracking

4. Dashboard
- Revenue MTD
- Active members
- At-risk members
- Expiry upcoming
- AI Insights banner

5. Business Health
- Revenue overview
- Retention %
- At risk %
- Expired %
- Action required section

6. AI Workouts
- Generate personalized workout plan
- Based on:
  - Goal
  - Experience
  - Weight
  - Height
  - Diet preference

7. AI Diet Plans
- Generate calorie-based plan
- Member specific

8. WhatsApp Automation
- Expiry reminders
- Payment reminders
- Inactive member nudges
- Birthday wishes
- Manual broadcast
- Message logs
- Cron-based automation (no Celery)

9. Branding
- Gym logo
- Brand color
- Font customization

---

RETENTION LOGIC

At Risk:
- No attendance in 10+ days
- Renewal due < 7 days
- Expired but not renewed

AI Insight example:
“10 members likely to churn based on attendance drops.”

---

IMPORTANT CONSTRAINTS

- Must run on 1GB RAM
- No heavy joins
- No synchronous bulk operations
- No sending thousands of messages in request-response cycle
- No Redis
- No Celery
- Use management commands + cron only
- When need we can increase this plan

Performance is critical.

---

DATA DESIGN RULES

- Every model has gym FK
- All queries filtered by gym
- Add DB indexes on:
  - gym
  - expiry_date
  - status
  - created_at
- Avoid N+1 queries
- Use select_related and prefetch_related

---

SECURITY

- Plan-based access control
- Pro-only features must redirect if unauthorized
- Validate phone numbers before WhatsApp send
- Prevent duplicate automation same day

---

SCALING STRATEGY (FUTURE)

If scale increases:
- Move to 2GB server
- Introduce Redis
- Introduce Celery
- Add async queue
- Separate worker node

But current version must work WITHOUT these.

---

BUSINESS MODEL

Target:
Small & mid-size gyms in India.

Pricing:
Starter – ₹799
Growth – ₹1299
Pro – ₹1999

Primary revenue growth:
- Upsell to Pro
- WhatsApp automation usage
- AI differentiation

---

DEVELOPMENT RULES FOR AI

When generating code:
1. Always check what already exists.
2. Do not duplicate models.
3. Follow Django best practices.
4. Keep infra lightweight.
5. Avoid unnecessary complexity.
6. Respect multi-tenant isolation.
7. Write optimized queries.
8. Suggest indexes where needed.
9. Keep memory usage low.

---

GOAL

GymEdge is not just gym software.
It is an AI wrapper around gym management that automates decisions and retention.

The system should feel:
- Intelligent
- Automated
- Premium
- Fast
- Lightweight

---

You are now fully aware of the GymEdge project.

Before generating any code:
- Analyze what exists
- Identify gaps
- Suggest architecture
- Then implement clean production-ready solutions.