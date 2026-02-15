# GymOps AI SaaS – Project Context

## Product Identity
This is a B2B SaaS platform for Indian gym owners.
The product focuses on operations automation, retention, renewals, and revenue optimization.

This is NOT:
- A generic fitness app
- A workout recommendation chatbot
- A consumer-facing app

This IS:
- An operations control system for gym owners
- A WhatsApp-first business intelligence tool
- A retention and revenue optimization engine

---

## Target Users
1. Gym Owner (Primary Decision Maker)
2. Gym Manager
3. Trainer (Limited Interaction)

The Owner must receive:
- Daily revenue summary
- Renewal alerts
- Retention risk alerts
- Revenue leakage detection

---

## Core KPIs
The system must always care about:

- Monthly Recurring Revenue (MRR)
- Renewal Rate
- Member Retention
- Attendance Frequency
- Trial to Paid Conversion
- Payment Delays

Every feature must improve one of these KPIs.

---

## Business Rules

- Member inactive > 7 days → Retention Risk
- Renewal due in < 3 days → High Priority
- No trainer interaction in 10 days → Engagement Risk
- Revenue drop > 10% month-on-month → Alert Owner

---

## Product Philosophy

- Owner-first design
- WhatsApp-first notifications
- Minimal dashboards
- No feature bloat
- Automation > manual reports
- Insights > data

---

## MVP Constraints

- No complex workout builder
- No calorie tracking
- No social feed
- No AI fitness coaching

Focus strictly on business automation.

---

## Technical Stack

Backend: Django
DB: PostgreSQL
Async: Celery
Multi-tenant architecture
AI used only for:
- Insight generation
- Alert explanation
- Recommendation summaries

AI must not override business rules.
