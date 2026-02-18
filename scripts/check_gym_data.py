
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.gyms.models import Gym
from apps.users.models import GymUser
from apps.leads.models import Lead

def check_data():
    print(f"{'Gym Name':<30} | {'ID':<5} | {'Leads':<5} | {'Users':<5}")
    print("-" * 60)
    for gym in Gym.objects.all():
        lead_count = Lead.objects.filter(gym=gym).count()
        user_count = GymUser.objects.filter(gym=gym).count()
        print(f"{gym.name:<30} | {str(gym.id):<5} | {lead_count:<5} | {user_count:<5}")

    print("\nUsers:")
    print(f"{'Username':<20} | {'Role':<10} | {'Gym'}")
    print("-" * 60)
    for user in GymUser.objects.all().select_related('gym')[:10]:
         gym_name = user.gym.name if user.gym else "None"
         print(f"{user.username:<20} | {user.role:<10} | {gym_name}")

if __name__ == '__main__':
    check_data()
