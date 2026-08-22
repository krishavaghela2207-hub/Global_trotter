from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import date, timedelta

from travel_planner.models import (
    UserProfile, Region, Country, City, ActivityCategory,
    Activity, Trip, TripStop, ItineraryItem, TripExpense,
    TripLike, TripComment, SavedDestination
)

class GlobeTrotterModelAndApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test_traveler',
            email='test@traveler.com',
            password='testpassword123',
            first_name='Test',
            last_name='Traveler'
        )
        self.region = Region.objects.create(name='Europe', code='EUR')
        self.country = Country.objects.create(name='France', code='FR', region=self.region, currency='EUR', flag_emoji='🇫🇷')
        self.city = City.objects.create(
            name='Paris',
            country=self.country,
            region=self.region,
            cost_index='$$$',
            popularity_score=98.0,
            description='City of Light',
            image_url='https://example.com/paris.jpg',
            avg_daily_cost=Decimal('180.00')
        )
        self.category = ActivityCategory.objects.create(name='Sightseeing', slug='sightseeing')
        self.activity = Activity.objects.create(
            city=self.city,
            category=self.category,
            title='Eiffel Tower Experience',
            description='Iconic monument',
            estimated_cost=Decimal('45.00'),
            duration_hours=2.5,
            rating=4.9,
            image_url='https://example.com/eiffel.jpg'
        )
        self.trip = Trip.objects.create(
            user=self.user,
            title='Parisian Spring Journey',
            description='Wonderful vacation in Paris',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
            total_budget=Decimal('2000.00'),
            status='ongoing'
        )
        self.stop = TripStop.objects.create(
            trip=self.trip,
            city=self.city,
            order=1,
            arrival_date=date.today(),
            departure_date=date.today() + timedelta(days=5),
            allocated_budget=Decimal('2000.00')
        )
        self.item = ItineraryItem.objects.create(
            trip_stop=self.stop,
            activity=self.activity,
            title='Eiffel Tower Experience',
            cost=Decimal('45.00'),
            day_number=1,
            category='activity'
        )

    def test_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'GlobeTrotter')

    def test_cities_api(self):
        response = self.client.get('/api/cities/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('cities', data)
        self.assertEqual(len(data['cities']), 1)
        self.assertEqual(data['cities'][0]['name'], 'Paris')

    def test_activities_api(self):
        response = self.client.get('/api/activities/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('activities', data)
        self.assertEqual(len(data['activities']), 1)
        self.assertEqual(data['activities'][0]['title'], 'Eiffel Tower Experience')

    def test_trip_detail_and_budget_api(self):
        response = self.client.get(f'/api/trips/{self.trip.id}/')
        self.assertEqual(response.status_code, 200)
        trip_data = response.json()
        self.assertEqual(trip_data['title'], 'Parisian Spring Journey')
        self.assertEqual(len(trip_data['stops']), 1)
        self.assertEqual(len(trip_data['stops'][0]['items']), 1)

        budget_response = self.client.get(f'/api/trips/{self.trip.id}/budget/')
        self.assertEqual(budget_response.status_code, 200)
        budget_data = budget_response.json()
        self.assertEqual(budget_data['total_spent'], 45.0)

    def test_trip_cloning(self):
        self.client.login(username='test_traveler', password='testpassword123')
        clone_response = self.client.post(f'/api/trips/{self.trip.id}/clone/')
        self.assertEqual(clone_response.status_code, 200)
        data = clone_response.json()
        self.assertTrue(data['success'])
        self.assertEqual(Trip.objects.filter(user=self.user).count(), 2)

    def test_auth_login_api(self):
        response = self.client.post(
            '/api/auth/login/',
            data={'username': 'test_traveler', 'password': 'testpassword123'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_currency_rates_api(self):
        response = self.client.get('/api/currency/rates/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('rates', data)
        self.assertIn('EUR', data['rates'])
        self.assertIn('JPY', data['rates'])

    def test_ai_generate_itinerary_api(self):
        response = self.client.post(
            '/api/ai/generate-itinerary/',
            data={'persona': 'luxury_gourmet', 'days': 5, 'budget_level': 'luxury'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('stops', data)

    def test_eco_score_api(self):
        response = self.client.get(f'/api/trips/{self.trip.id}/eco/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('eco_score', data)
        self.assertIn('total_co2_kg', data)

    def test_packing_checklist_api(self):
        response = self.client.get(f'/api/trips/{self.trip.id}/packing/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('categories', data)
        self.assertGreater(data['total_count'], 0)

