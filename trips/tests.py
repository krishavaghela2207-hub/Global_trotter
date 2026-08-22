from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
from accounts.models import Profile, WishlistDestination
from destinations.models import Country, City, Activity
from trips.models import Trip, TripStop, ScheduledActivity, TripExpense, TripReview, TripComment, TripLike, TripCloneLog
from analytics.models import ActivityLog

class GlobeTrotterFullWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Country and City
        self.country = Country.objects.create(name='Japan', code='JP', continent='Asia', currency='JPY')
        self.city_tokyo = City.objects.create(
            country=self.country,
            name='Tokyo',
            description='Futuristic and historic city',
            cost_index='MODERATE',
            avg_daily_cost=140.00,
            popularity_score=98,
            latitude=35.6762,
            longitude=139.6503
        )
        self.city_kyoto = City.objects.create(
            country=self.country,
            name='Kyoto',
            description='Ancient temples and cultural capital',
            cost_index='MODERATE',
            avg_daily_cost=120.00,
            popularity_score=95,
            latitude=35.0116,
            longitude=135.7681
        )

        # Create Activity
        self.activity_shibuya = Activity.objects.create(
            city=self.city_tokyo,
            name='Shibuya Crossing & Food Tour',
            category='FOOD',
            estimated_cost=45.00,
            duration_hours=3.0
        )

        # Create Regular User
        self.user = User.objects.create_user(username='testtraveler', email='test@travel.com', password='Password123')
        self.profile = self.user.profile
        self.profile.is_email_verified = True
        self.profile.travel_style = 'SOLO'
        self.profile.save()

        # Create Second User for social interactions
        self.friend = User.objects.create_user(username='friendtraveler', email='friend@travel.com', password='Password123')
        self.friend.profile.is_email_verified = True
        self.friend.profile.save()

        # Create Admin User
        self.admin = User.objects.create_superuser(username='adminuser', email='admin@travel.com', password='Password123')

    def test_user_authentication_and_email_verification(self):
        # Register new user
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'Explorer',
            'email': 'new@travel.com',
            'password': 'StrongPassword123',
            'confirm_password': 'StrongPassword123',
            'travel_style': 'ADVENTURE',
            'budget_tier': 'BUDGET',
        })
        self.assertEqual(response.status_code, 200) # Renders verify_email_sent.html
        
        new_user = User.objects.get(username='newuser')
        self.assertFalse(new_user.profile.is_email_verified)
        token = new_user.profile.verification_token
        self.assertTrue(len(token) > 10)

        # Verify email using token
        verify_response = self.client.get(reverse('verify_email'), {'token': token})
        self.assertEqual(verify_response.status_code, 302) # Redirects to dashboard
        new_user.profile.refresh_from_db()
        self.assertTrue(new_user.profile.is_email_verified)

    def test_wishlist_toggle_api(self):
        self.client.login(username='testtraveler', password='Password123')
        response = self.client.post(reverse('api_wishlist_toggle', kwargs={'city_id': self.city_tokyo.id}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['is_wishlisted'])
        self.assertEqual(data['total_wishlist'], 1)

        # Untoggle
        response_untoggle = self.client.post(reverse('api_wishlist_toggle', kwargs={'city_id': self.city_tokyo.id}))
        self.assertFalse(response_untoggle.json()['is_wishlisted'])
        self.assertEqual(response_untoggle.json()['total_wishlist'], 0)

    def test_trip_creation_and_budget_calculation(self):
        self.client.login(username='testtraveler', password='Password123')
        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=6)

        # Create Trip
        create_res = self.client.post(reverse('trip_create'), {
            'title': 'Japan Golden Tour',
            'description': 'Tokyo and Kyoto adventure',
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d'),
            'estimated_budget': '1500.00',
            'currency': 'USD',
            'travel_style': 'SOLO',
            'is_public': True,
        })
        self.assertEqual(create_res.status_code, 302)
        trip = Trip.objects.get(title='Japan Golden Tour')
        self.assertEqual(trip.user, self.user)
        self.assertEqual(trip.duration_days, 7)

        # Add Stop 1: Tokyo
        stop1_res = self.client.post(reverse('add_stop', kwargs={'pk': trip.id}), {
            'city': self.city_tokyo.id,
            'arrival_date': start.strftime('%Y-%m-%d'),
            'departure_date': (start + timedelta(days=3)).strftime('%Y-%m-%d'),
            'accommodation_name': 'Tokyo Hotel',
            'stay_cost': '300.00',
            'transport_to_stop_type': 'FLIGHT',
            'transport_cost': '400.00',
        })
        self.assertEqual(stop1_res.status_code, 302)
        stop1 = TripStop.objects.get(trip=trip, city=self.city_tokyo)

        # Add Scheduled Activity
        act_res = self.client.post(reverse('add_activity', kwargs={'pk': trip.id}), {
            'stop': stop1.id,
            'activity': self.activity_shibuya.id,
            'title': 'Shibuya Crossing & Food Tour',
            'category': 'FOOD',
            'scheduled_date': start.strftime('%Y-%m-%d'),
            'start_time': '18:00',
            'duration_minutes': 180,
            'cost': '45.00',
        })
        self.assertEqual(act_res.status_code, 302)

        # Add Logged Expense
        exp_res = self.client.post(reverse('trip_budget', kwargs={'pk': trip.id}), {
            'category': 'MEAL',
            'title': 'Ramen Dinner',
            'amount': '25.00',
            'expense_date': start.strftime('%Y-%m-%d'),
        })
        self.assertEqual(exp_res.status_code, 302)

        # Check total costs: Stay ($300) + Transport ($400) + Activity ($45) + Expense ($25) = $770
        self.assertEqual(trip.calculated_total_cost, 770.00)
        self.assertEqual(trip.budget_remaining, 730.00)
        self.assertFalse(trip.is_over_budget)

    def test_trip_clone_copy_functionality(self):
        # Create initial trip by user
        start = date.today() + timedelta(days=10)
        end = start + timedelta(days=5)
        trip = Trip.objects.create(
            user=self.user,
            title="Tokyo Blitz",
            start_date=start,
            end_date=end,
            estimated_budget=1000.00,
            is_public=True
        )
        stop = TripStop.objects.create(
            trip=trip,
            city=self.city_tokyo,
            arrival_date=start,
            departure_date=end,
            stay_cost=200.00
        )
        ScheduledActivity.objects.create(
            stop=stop,
            title="Tour",
            scheduled_date=start,
            cost=50.00
        )

        # Friend clones the trip
        self.client.login(username='friendtraveler', password='Password123')
        copy_res = self.client.get(reverse('copy_trip', kwargs={'pk': trip.id}))
        self.assertEqual(copy_res.status_code, 302)

        # Verify cloned trip exists under friend
        cloned_trip = Trip.objects.filter(user=self.friend, cloned_from=trip).first()
        self.assertIsNotNone(cloned_trip)
        self.assertEqual(cloned_trip.title, "Copy of Tokyo Blitz")
        self.assertEqual(cloned_trip.stops.count(), 1)
        self.assertEqual(ScheduledActivity.objects.filter(stop__trip=cloned_trip).count(), 1)

    def test_trip_reviews_and_live_comments(self):
        start = date.today() + timedelta(days=10)
        end = start + timedelta(days=5)
        trip = Trip.objects.create(user=self.user, title="Public Trip", start_date=start, end_date=end, is_public=True)

        # Friend submits review
        self.client.login(username='friendtraveler', password='Password123')
        review_res = self.client.post(reverse('post_review', kwargs={'pk': trip.id}), {
            'rating': 5,
            'title': 'Great plan!',
            'comment': 'Awesome itinerary!'
        })
        self.assertEqual(review_res.status_code, 302)
        self.assertEqual(trip.reviews.count(), 1)
        self.assertEqual(trip.average_rating, 5.0)

        # Friend submits AJAX comment
        comment_res = self.client.post(
            reverse('post_comment', kwargs={'pk': trip.id}),
            {'content': 'Are reservations needed for this tour?'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(comment_res.status_code, 200)
        data = comment_res.json()
        self.assertTrue(data['success'])
        self.assertEqual(trip.comments.count(), 1)

    def test_live_feed_api(self):
        ActivityLog.objects.create(
            user=self.user,
            event_type='TRIP_CREATE',
            title='Test live event',
            description='Testing feed API'
        )
        response = self.client.get(reverse('api_live_feed'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['count'] >= 1)
        self.assertEqual(data['activities'][0]['title'], 'Test live event')

    def test_admin_dashboard_access_control(self):
        # Regular user cannot access admin dashboard
        self.client.login(username='testtraveler', password='Password123')
        denied_res = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(denied_res.status_code, 302) # Redirect to login

        # Admin user can access
        self.client.login(username='adminuser', password='Password123')
        admin_res = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(admin_res.status_code, 200)
        self.assertContains(admin_res, "GlobeTrotter Platform Command Center")
