from django.core.management.base import BaseCommand
from apps.users.models import GymUser
from apps.gyms.models import Gym
from apps.enterprises.models import HoldingCompany, Brand, Organization


class Command(BaseCommand):
    help = 'Create test users for authentication testing'

    def handle(self, *args, **options):
        TEST_PASSWORD = "Qwerty@123"
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('Creating Test Users for Authentication Testing'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # 1. Update existing users
        self.stdout.write('\n1. Setting passwords for existing users...')
        users_to_update = [
            ('standard-owner', 'owner1@pinkgym.com'),
            ('royalty-tester', 'royalty@gymedge.com'),
            ('franchise-owner', 'franchise@gymedge.com'),
            ('holding-admin', 'holding@gymedge.com'),
            ('rajesh-meena', 'rajesh@pinkgym.com'),
            ('john-iron', 'mahesh@gmail.com'),
        ]
        
        for username, email in users_to_update:
            user = GymUser.objects.filter(username=username).first()
            if user:
                user.email = email
                user.set_password(TEST_PASSWORD)
                user.save()
                self.stdout.write(f'   ✓ Updated {username:20} - Email: {email}')
            else:
                self.stdout.write(self.style.WARNING(f'   ✗ User not found: {username}'))
        
        # 2. Create Brand Admin
        self.stdout.write('\n2. Creating Brand Admin...')
        brand = Brand.objects.filter(brand_code='GE_GEN').first()
        holding = HoldingCompany.objects.filter(holding_code='HOLD895906').first()
        
        if brand:
            brand_admin, created = GymUser.objects.get_or_create(
                username='brand-admin',
                defaults={
                    'phone': '9828066666',
                    'name': 'Brand Administrator',
                    'email': 'brand@gymedge.com',
                    'role': 'brand_admin',
                    'brand': brand,
                    'holding_company': holding,
                    'is_active': True,
                }
            )
            brand_admin.email = 'brand@gymedge.com'
            brand_admin.brand = brand
            brand_admin.holding_company = holding
            brand_admin.set_password(TEST_PASSWORD)
            brand_admin.save()
            
            if created:
                self.stdout.write(f'   ✓ Created brand-admin - Email: brand@gymedge.com')
            else:
                self.stdout.write(f'   ✓ Updated brand-admin - Email: brand@gymedge.com')
        else:
            self.stdout.write(self.style.WARNING("   ✗ Brand 'GE_GEN' not found"))
        
        # 3. Create Gym Staff Users
        self.stdout.write('\n3. Creating Gym Staff Users (Pink City Strength)...')
        gym = Gym.objects.filter(gym_code='GYM3242383').first()
        
        if gym:
            staff_users = [
                {
                    'username': 'pink-manager',
                    'phone': '9876501010',
                    'name': 'Amit Sharma',
                    'email': 'amit@pinkgym.com',
                    'role': 'manager',
                    'can_view_revenue': True,
                },
                {
                    'username': 'pink-trainer1',
                    'phone': '9876501011',
                    'name': 'Priya Singh',
                    'email': 'priya@pinkgym.com',
                    'role': 'trainer',
                },
                {
                    'username': 'pink-trainer2',
                    'phone': '9876501012',
                    'name': 'Rahul Verma',
                    'email': 'rahul@pinkgym.com',
                    'role': 'trainer',
                },
                {
                    'username': 'pink-receptionist',
                    'phone': '9876501013',
                    'name': 'Kavita Joshi',
                    'email': 'kavita@pinkgym.com',
                    'role': 'receptionist',
                    'can_use_ai': False,
                },
            ]
            
            for staff_data in staff_users:
                user,created = GymUser.objects.get_or_create(
                    username=staff_data['username'],
                    defaults={
                        'phone': staff_data['phone'],
                        'name': staff_data['name'],
                        'email': staff_data['email'],
                        'role': staff_data['role'],
                        'gym': gym,
                        'is_active': True,
                        'can_manage_members': True,
                        'can_view_revenue': staff_data.get('can_view_revenue', False),
                        'can_use_ai': staff_data.get('can_use_ai', True),
                    }
                )
                user.email = staff_data['email']
                user.gym = gym
                user.role = staff_data['role']
                user.set_password(TEST_PASSWORD)
                user.save()
                
                if created:
                    self.stdout.write(f"   ✓ Created {staff_data['username']:20} - {staff_data['role']:15}")
                else:
                    self.stdout.write(f"   ✓ Updated {staff_data['username']:20} - {staff_data['role']:15}")
        else:
            self.stdout.write(self.style.WARNING("   ✗ Gym 'Pink City Strength' not found"))
        
        # 4. Summary
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('TEST CREDENTIALS SUMMARY'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'Test Password: {TEST_PASSWORD}')
        self.stdout.write(f'Development OTP: 123456')
        self.stdout.write('\nEntity Codes:')
        self.stdout.write('  - Pink City Strength: GYM3242383')
        self.stdout.write('  - Holding Company: HOLD895906')
        self.stdout.write('  - Brand: GE_GEN')
        self.stdout.write('  - Organization: ORG822407')
        self.stdout.write('\nLogin URLs:')
        self.stdout.write('  - Main Login: http://127.0.0.1:8000/auth/login/')
        self.stdout.write('  - Enterprise Login: http://127.0.0.1:8000/enterprise/login/')
        self.stdout.write('=' * 80)
