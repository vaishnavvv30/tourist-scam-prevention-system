"""Seed the database with sample data for demonstration."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from scams.models import ScamReport, Location
from vendors.models import Vendor, Review
from alerts.models import ScamAlert
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Seed database with sample scam reports, vendors, and alerts'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # Create test user if not exists
        user, created = User.objects.get_or_create(
            username='tourist_demo',
            defaults={
                'email': 'demo@scamguard.ai',
                'first_name': 'Demo',
                'last_name': 'Tourist',
            }
        )
        if created:
            user.set_password('demo12345')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created demo user: tourist_demo / demo12345'))

        # Locations
        locations_data = [
            {'name': 'Connaught Place', 'city': 'Delhi', 'country': 'India', 'latitude': 28.6315, 'longitude': 77.2167},
            {'name': 'Jaipur Old City', 'city': 'Jaipur', 'country': 'India', 'latitude': 26.9124, 'longitude': 75.7873},
            {'name': 'Colaba Causeway', 'city': 'Mumbai', 'country': 'India', 'latitude': 18.9067, 'longitude': 72.8147},
            {'name': 'MG Road', 'city': 'Bangalore', 'country': 'India', 'latitude': 12.9716, 'longitude': 77.5946},
            {'name': 'Khao San Road', 'city': 'Bangkok', 'country': 'Thailand', 'latitude': 13.7590, 'longitude': 100.4974},
            {'name': 'Bali Beach Area', 'city': 'Bali', 'country': 'Indonesia', 'latitude': -8.3405, 'longitude': 115.0920},
        ]

        locations = []
        for loc_data in locations_data:
            loc, _ = Location.objects.get_or_create(
                name=loc_data['name'],
                defaults={**loc_data, 'risk_score': random.uniform(30, 85), 'total_reports': random.randint(5, 50)}
            )
            locations.append(loc)

        # Scam Reports
        reports_data = [
            {'title': 'Taxi driver used rigged meter', 'description': 'The taxi driver from Delhi airport used a tampered meter. The fare showed ₹1500 for a 15km ride that should cost around ₹300. The meter was running extremely fast.', 'category': 'taxi', 'severity': 'high', 'charged_amount': 1500, 'expected_amount': 300, 'scam_probability': 91},
            {'title': 'Restaurant double-charged for items', 'description': 'A restaurant in Jaipur old city charged us twice for water bottles and added a mysterious "service enhancement fee" of ₹500.', 'category': 'restaurant', 'severity': 'medium', 'charged_amount': 2800, 'expected_amount': 1200, 'scam_probability': 78},
            {'title': 'Fake tour guide at Taj Mahal', 'description': 'A man claiming to be an official guide at the Taj Mahal charged ₹3000 for a 30-minute tour. He had no official ID and provided incorrect historical information.', 'category': 'tour_guide', 'severity': 'high', 'charged_amount': 3000, 'expected_amount': 500, 'scam_probability': 88},
            {'title': 'Overpriced souvenirs near Gateway of India', 'description': 'Street vendor in Colaba sold "genuine silk" scarf for ₹2500 that turned out to be polyester worth ₹200.', 'category': 'shopping', 'severity': 'medium', 'charged_amount': 2500, 'expected_amount': 200, 'scam_probability': 85},
            {'title': 'Tuk-tuk overcharge in Bangkok', 'description': 'Tuk-tuk driver quoted 500 THB for a ride that normally costs 50 THB. Took a much longer route through traffic.', 'category': 'taxi', 'severity': 'high', 'charged_amount': 500, 'expected_amount': 50, 'scam_probability': 92},
            {'title': 'Currency exchange scam', 'description': 'Money changer in MG Road gave wrong exchange rate and counted bills to confuse. Lost approximately ₹2000 in the exchange.', 'category': 'currency', 'severity': 'critical', 'charged_amount': 5000, 'expected_amount': 3000, 'scam_probability': 95},
            {'title': 'Hotel booking bait and switch', 'description': 'Booked a deluxe room but was given a much smaller basic room. When complained, was told the room in photos was "not available".', 'category': 'accommodation', 'severity': 'medium', 'charged_amount': 4500, 'expected_amount': 2000, 'scam_probability': 72},
            {'title': 'Fake temple donation scam', 'description': 'Near a temple, was approached by someone claiming donations were mandatory and asked for ₹5000. Later found out it was a scam.', 'category': 'other', 'severity': 'high', 'charged_amount': 5000, 'expected_amount': 0, 'scam_probability': 96},
        ]

        for i, report_data in enumerate(reports_data):
            loc = locations[i % len(locations)]
            prob = report_data.pop('scam_probability')
            report, created = ScamReport.objects.get_or_create(
                title=report_data['title'],
                defaults={
                    **report_data,
                    'user': user,
                    'location': loc,
                    'location_name': f"{loc.name}, {loc.city}",
                    'latitude': loc.latitude + random.uniform(-0.01, 0.01),
                    'longitude': loc.longitude + random.uniform(-0.01, 0.01),
                    'scam_probability': prob,
                    'ai_risk_score': prob / 10,
                    'ai_summary': f'AI analysis indicates a {prob}% probability of fraud. This report matches patterns commonly associated with {report_data["category"]} scams in this region.',
                    'is_ai_analyzed': True,
                    'upvotes': random.randint(5, 50),
                    'views_count': random.randint(20, 200),
                    'incident_date': date.today() - timedelta(days=random.randint(1, 60)),
                }
            )

        # Vendors
        vendors_data = [
            {'name': 'Delhi Heritage Tours', 'category': 'tour_guide', 'city': 'Delhi', 'country': 'India', 'latitude': 28.6139, 'longitude': 77.2090, 'description': 'Government-certified heritage walking tours of Old Delhi.', 'is_verified': True, 'trust_score': 92, 'safety_rating': 4.8},
            {'name': 'Raju Taxi Service', 'category': 'taxi', 'city': 'Jaipur', 'country': 'India', 'latitude': 26.9124, 'longitude': 75.7873, 'description': 'Reliable metered taxi service with GPS tracking.', 'is_verified': True, 'trust_score': 88, 'safety_rating': 4.5},
            {'name': 'Masala Kitchen', 'category': 'restaurant', 'city': 'Mumbai', 'country': 'India', 'latitude': 18.9220, 'longitude': 72.8347, 'description': 'Authentic Indian cuisine with transparent pricing.', 'is_verified': True, 'trust_score': 95, 'safety_rating': 4.9},
            {'name': 'Silk Palace Boutique', 'category': 'shop', 'city': 'Jaipur', 'country': 'India', 'latitude': 26.9196, 'longitude': 75.7878, 'description': 'Genuine handloom silk products with certification.', 'is_verified': True, 'trust_score': 85, 'safety_rating': 4.3},
            {'name': 'Bangkok Safe Rides', 'category': 'taxi', 'city': 'Bangkok', 'country': 'Thailand', 'latitude': 13.7563, 'longitude': 100.5018, 'description': 'App-based metered taxi service.', 'is_verified': True, 'trust_score': 90, 'safety_rating': 4.6},
            {'name': 'Bali Beach Resort', 'category': 'hotel', 'city': 'Bali', 'country': 'Indonesia', 'latitude': -8.3405, 'longitude': 115.0920, 'description': 'Trusted beachfront accommodation.', 'is_verified': False, 'trust_score': 72, 'safety_rating': 3.8},
        ]

        for v_data in vendors_data:
            Vendor.objects.get_or_create(
                name=v_data['name'],
                defaults={
                    **v_data,
                    'added_by': user,
                    'total_reviews': random.randint(10, 100),
                    'positive_reviews': random.randint(8, 80),
                    'negative_reviews': random.randint(0, 5),
                    'price_range': random.choice(['$', '$$', '$$$']),
                    'opening_hours': '9:00 AM - 9:00 PM',
                }
            )

        # Alerts
        alerts_data = [
            {'title': 'Taxi Scam Surge at Delhi Airport', 'description': 'Multiple reports of rigged taxi meters at IGI Airport Terminal 3. Use pre-paid taxi booths or Uber/Ola.', 'alert_level': 'danger', 'city': 'Delhi', 'category': 'taxi', 'reports_count': 15, 'affected_tourists': 23},
            {'title': 'Fake Tour Guides at Amber Fort', 'description': 'Unauthorized individuals posing as official guides near Amber Fort entrance. Always verify ID cards.', 'alert_level': 'warning', 'city': 'Jaipur', 'category': 'tour_guide', 'reports_count': 8, 'affected_tourists': 12},
            {'title': 'Currency Exchange Fraud on MG Road', 'description': 'Several money changers on MG Road reported for giving wrong exchange rates. Use banks or ATMs instead.', 'alert_level': 'critical', 'city': 'Bangalore', 'category': 'currency', 'reports_count': 22, 'affected_tourists': 35},
        ]

        for a_data in alerts_data:
            ScamAlert.objects.get_or_create(
                title=a_data['title'],
                defaults={**a_data, 'is_active': True, 'auto_generated': True}
            )

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write(f'  Reports: {ScamReport.objects.count()}')
        self.stdout.write(f'  Vendors: {Vendor.objects.count()}')
        self.stdout.write(f'  Locations: {Location.objects.count()}')
        self.stdout.write(f'  Alerts: {ScamAlert.objects.count()}')
