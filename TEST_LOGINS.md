# 🧪 Test Login Credentials — Ryan's Gym & Fitness Club

> **Gym Code:** `GYM0000001`
> **OTP (Dev Mode):** `123456`
> **Login URL:** [http://127.0.0.1:8099/login/](http://127.0.0.1:8099/login/)

## Staff Users

| Role | Name | Phone | Email |
|------|------|-------|-------|
| **Owner** | Sunil Sharma | `9928122572` | sunil@ryangym.in |
| **Manager** | Amit Rathore | `9876501005` | amit@ryangym.in |
| **Trainer** | Vikram Singh | `9876501001` | vikram@ryangym.in |
| **Trainer** | Priya Meena | `9876501002` | priya@ryangym.in |
| **Trainer** | Rohit Yadav | `9876501003` | rohit@ryangym.in |
| **Receptionist** | Kavita Joshi | `9876501004` | kavita@ryangym.in |

## Login Steps

1. Enter gym code: `GYM0000001` → Continue
2. Enter phone number from table above → Send OTP
3. Enter OTP: `123456` → Verify & Login

## Role Access

| Feature | Owner | Manager | Trainer | Receptionist |
|---------|:-----:|:-------:|:-------:|:------------:|
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| Members | ✅ | ✅ | ✅ | ✅ |
| Settings/Branding | ✅ | ❌ | ❌ | ❌ |
| View Revenue | ✅ | ✅ | ❌ | ❌ |
| AI Features | ✅ | ✅ | ✅ | ❌ |

## Re-seed Data

```bash
python manage.py seed_demo_data
```
