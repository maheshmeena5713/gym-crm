# GymEdge - AI SaaS for Gyms 🏋️‍♂️🚀

GymEdge is a B2B SaaS platform designed to help gym owners automate operations, improve retention, and maximize revenue.

## 🌟 Key Features

### Core SaaS
*   **Member Management:** Track memberships, renewals, and attendance.
*   **AI Insights:** Churn risk prediction and automated recovery suggestions.
*   **WhatsApp Integration:** Automated welcome messages and renewal reminders.
*   **Billing:** Subscription management and invoicing.

### 🏢 Enterprise Upgrade (New!)
Support for Multi-Brand Portfolios and Franchise Operations.
*   **Hierarchy:** `Holding Company` -> `Brand` -> `Organization` -> `Location`.
*   **RBAC:** specialized roles for Holding Admins, Brand Managers, and Franchise Owners.
*   **Consolidated Dashboards:** Real-time aggregation of stats across all locations.
*   **Royalty Tracking:** Automated calculation of franchise royalties.

👉 **[Read the Enterprise Admin Guide](ENTERPRISE_GUIDE.md)**
👉 **[View the Product Flow Diagram](PRODUCT_FLOW.md)**

## 🛠️ Technical Stack
*   **Backend:** Django 5.x, Python 3.x
*   **Database:** PostgreSQL
*   **API:** Django REST Framework (DRF)
*   **Frontend:** Django Templates + Tailwind CSS + Vanilla JS
*   **AI:** Google Gemini / OpenAI Integration

## 🚀 Getting Started

### Prerequisites
*   Python 3.10+
*   PostgreSQL
*   Redis (for Celery)

### Installation
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-org/gym-crm.git
    cd gym-crm
    ```
2.  **Create Virtual Environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Setup Environment Variables:**
    Copy `.env.example` to `.env` and configure your DB and API keys.

5.  **Run Migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Create Superuser:**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run Server:**
    ```bash
    python manage.py runserver
    ```

## 🧪 Running Tests
Run the full test suite to verify system integrity:
```bash
python manage.py test
```

## 📂 Project Structure
*   `apps/` - Django apps (users, gyms, members, enterprises, etc.)
*   `config/` - Project settings and URL configuration
*   `templates/` - Global HTML templates
*   `static/` - CSS, JS, and images
