import os
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile, WishlistDestination
from destinations.models import Country, City, Activity
from trips.models import Trip, TripStop, ScheduledActivity, TripExpense, TripReview, TripComment, TripLike, TripCloneLog
from analytics.models import ActivityLog

class Command(BaseCommand):
    help = "Seeds comprehensive Indian & global destinations, activities, INR currency, and multi-city itineraries."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting GlobeTrotter enhanced database seeding..."))

        # 1. Create or Update Users
        admin_user, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@globetrotter.com', 'first_name': 'Admin', 'last_name': 'Commander', 'is_staff': True, 'is_superuser': True})
        admin_user.set_password('Admin@12345')
        admin_user.save()
        admin_profile = admin_user.profile
        admin_profile.is_email_verified = True
        admin_profile.is_admin_role = True
        admin_profile.preferred_currency = 'INR'
        admin_profile.travel_style = 'LUXURY'
        admin_profile.save()

        traveler, _ = User.objects.get_or_create(username='traveler', defaults={'email': 'traveler@globetrotter.com', 'first_name': 'Aarav', 'last_name': 'Sharma'})
        traveler.set_password('Traveler@12345')
        traveler.save()
        traveler_profile = traveler.profile
        traveler_profile.is_email_verified = True
        traveler_profile.preferred_currency = 'INR'
        traveler_profile.travel_style = 'ADVENTURE'
        traveler_profile.bio = "Passionate explorer traveling across the Himalayas, Kashmir valleys, Gujarat heritage, and world cultural capitals."
        traveler_profile.avatar_url = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&auto=format&fit=crop&q=80"
        traveler_profile.save()

        sarah, _ = User.objects.get_or_create(username='sarah_explorer', defaults={'email': 'sarah@globetrotter.com', 'first_name': 'Sarah', 'last_name': 'Jenkins'})
        sarah.set_password('Sarah@12345')
        sarah.save()
        sarah.profile.is_email_verified = True
        sarah.profile.preferred_currency = 'INR'
        sarah.profile.travel_style = 'COUPLE'
        sarah.profile.avatar_url = "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&auto=format&fit=crop&q=80"
        sarah.profile.save()

        rohit, _ = User.objects.get_or_create(username='rohit_kashmiri', defaults={'email': 'rohit@globetrotter.com', 'first_name': 'Rohit', 'last_name': 'Patel'})
        rohit.set_password('Rohit@12345')
        rohit.save()
        rohit.profile.is_email_verified = True
        rohit.profile.preferred_currency = 'INR'
        rohit.profile.travel_style = 'FAMILY'
        rohit.profile.avatar_url = "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&auto=format&fit=crop&q=80"
        rohit.profile.save()

        self.stdout.write(self.style.SUCCESS("[OK] Users created."))

        # 2. Create Countries
        countries_data = [
            ('India', 'IN', 'Asia', 'INR'),
            ('Japan', 'JP', 'Asia', 'JPY'),
            ('France', 'FR', 'Europe', 'EUR'),
            ('Italy', 'IT', 'Europe', 'EUR'),
            ('Indonesia', 'ID', 'Asia', 'IDR'),
            ('Spain', 'ES', 'Europe', 'EUR'),
            ('United States', 'US', 'North America', 'USD'),
            ('Switzerland', 'CH', 'Europe', 'CHF'),
            ('Australia', 'AU', 'Oceania', 'AUD'),
            ('United Arab Emirates', 'AE', 'Asia', 'AED'),
        ]

        country_map = {}
        for name, code, cont, curr in countries_data:
            c, _ = Country.objects.get_or_create(name=name, defaults={'code': code, 'continent': cont, 'currency': curr})
            country_map[name] = c

        # 3. Create Cities (Indian States + Global Hubs)
        cities_data = [
            # === INDIA: Kashmir ===
            {
                'country': 'India',
                'state_or_region': 'Kashmir',
                'name': 'Srinagar',
                'description': 'Paradise on Earth: iconic Dal Lake wooden houseboats, vibrant Shikara rides, floating vegetable markets, and Mughal royal gardens.',
                'image_url': 'https://images.unsplash.com/photo-1566837945700-30057527ade0?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'MODERATE',
                'popularity_score': 99,
                'latitude': 34.0837,
                'longitude': 74.7973,
                'best_season': 'April - October & Winter Snow',
                'avg_daily_cost': 3500.00
            },
            {
                'country': 'India',
                'state_or_region': 'Kashmir',
                'name': 'Gulmarg',
                'description': 'Meadow of Flowers famous for the world-class Gulmarg Gondola, Apharwat snow peaks, pine-fringed alpine slopes, and skiing resorts.',
                'image_url': 'https://images.unsplash.com/photo-1595846519845-68e298c2edd8?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'MODERATE',
                'popularity_score': 97,
                'latitude': 34.0484,
                'longitude': 74.3805,
                'best_season': 'December - March (Snow) & May - September',
                'avg_daily_cost': 4500.00
            },
            {
                'country': 'India',
                'state_or_region': 'Kashmir',
                'name': 'Pahalgam',
                'description': 'Valley of Shepherds surrounded by Lidder river streams, Betaab Valley, Aru Valley pine forests, and picturesque trekking basecamps.',
                'image_url': 'https://images.unsplash.com/photo-1601000938259-9e92002320b2?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'MODERATE',
                'popularity_score': 95,
                'latitude': 34.0153,
                'longitude': 75.3255,
                'best_season': 'March - November',
                'avg_daily_cost': 3200.00
            },

            # === INDIA: Himachal Pradesh ===
            {
                'country': 'India',
                'state_or_region': 'Himachal Pradesh',
                'name': 'Manali',
                'description': 'Himalayan adventure hub surrounded by snow-capped peaks, Solang Valley paragliding, Rohtang Pass, hot springs, and Old Manali riverside cafes.',
                'image_url': 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'MODERATE',
                'popularity_score': 98,
                'latitude': 32.2396,
                'longitude': 77.1887,
                'best_season': 'October - June',
                'avg_daily_cost': 3000.00
            },
            {
                'country': 'India',
                'state_or_region': 'Himachal Pradesh',
                'name': 'Shimla',
                'description': 'Queen of Hills: historic British colonial architecture, the Mall Road, scenic Ridge viewpoints, and the UNESCO Kalka-Shimla Toy Train.',
                'image_url': 'https://images.unsplash.com/photo-1597074866923-dc0589150358?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'MODERATE',
                'popularity_score': 94,
                'latitude': 31.1048,
                'longitude': 77.1734,
                'best_season': 'March - June & Winter Snow',
                'avg_daily_cost': 2800.00
            },
            {
                'country': 'India',
                'state_or_region': 'Himachal Pradesh',
                'name': 'Dharamshala & Bir Billing',
                'description': 'Spiritual home of Dalai Lama in McLeod Ganj, surrounded by cedar forests, Triund mountain trek, and world-renowned Bir Billing paragliding.',
                'image_url': 'https://images.unsplash.com/photo-1571401835393-8c5f35328320?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'BUDGET',
                'popularity_score': 93,
                'latitude': 32.2190,
                'longitude': 76.3234,
                'best_season': 'September - June',
                'avg_daily_cost': 2200.00
            },

            # === INDIA: Gujarat ===
            {
                'country': 'India',
                'state_or_region': 'Gujarat',
                'name': 'Ahmedabad',
                'description': 'India first UNESCO World Heritage City: Sabarmati Ashram, intricately carved Adalaj Stepwell, Sidi Saiyyed Mosque, and legendary Manek Chowk night street food.',
                'image_url': 'https://images.unsplash.com/photo-1609137144822-094ba470ec9e?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'BUDGET',
                'popularity_score': 96,
                'latitude': 23.0225,
                'longitude': 72.5714,
                'best_season': 'October - March',
                'avg_daily_cost': 2400.00
            },
            {
                'country': 'India',
                'state_or_region': 'Gujarat',
                'name': 'Rann of Kutch',
                'description': 'The mesmerizing Great Rann White Desert, famous for the vibrant Rann Utsav festival, full-moon night spectacles, Kutchi handicrafts, and desert safaris.',
                'image_url': 'https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'MODERATE',
                'popularity_score': 97,
                'latitude': 23.8340,
                'longitude': 69.8385,
                'best_season': 'November - February (Rann Utsav)',
                'avg_daily_cost': 3800.00
            },
            {
                'country': 'India',
                'state_or_region': 'Gujarat',
                'name': 'Gir National Park & Somnath',
                'description': 'The sole sanctuary of the majestic Asiatic Lion in Gir, combined with the sacred seaside Somnath Jyotirlinga Temple on the Arabian Sea coast.',
                'image_url': 'https://images.unsplash.com/photo-1534177616072-ef7dc120449d?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'MODERATE',
                'popularity_score': 92,
                'latitude': 21.1243,
                'longitude': 70.8242,
                'best_season': 'November - March',
                'avg_daily_cost': 3200.00
            },
            {
                'country': 'India',
                'state_or_region': 'Gujarat',
                'name': 'Statue of Unity (Kevadia)',
                'description': 'World tallest monument standing at 182 meters, featuring observation deck, Valley of Flowers, river rafting, and evening laser projection shows.',
                'image_url': 'https://images.unsplash.com/photo-1588416936097-41850ab3d86d?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'BUDGET',
                'popularity_score': 95,
                'latitude': 21.8380,
                'longitude': 73.7191,
                'best_season': 'October - March',
                'avg_daily_cost': 2600.00
            },

            # === INDIA: Rajasthan, Ladakh, Kerala, Goa ===
            {
                'country': 'India',
                'state_or_region': 'Rajasthan',
                'name': 'Jaipur & Udaipur',
                'description': 'Royal palaces, grand Amber Fort, romantic Lake Pichola boat cruises, and colorful Rajasthani cultural heritage.',
                'image_url': 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'MODERATE',
                'popularity_score': 98,
                'latitude': 26.9124,
                'longitude': 75.7873,
                'best_season': 'October - March',
                'avg_daily_cost': 3200.00
            },
            {
                'country': 'India',
                'state_or_region': 'Ladakh',
                'name': 'Leh Ladakh',
                'description': 'High altitude Himalayan moonland: turquoise Pangong Tso Lake, Nubra Valley sand dunes, and thrilling Khardung La motorcycling pass.',
                'image_url': 'https://images.unsplash.com/photo-1581793745862-99fde7fa73d2?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'MODERATE',
                'popularity_score': 99,
                'latitude': 34.1526,
                'longitude': 77.5771,
                'best_season': 'May - September',
                'avg_daily_cost': 4000.00
            },
            {
                'country': 'India',
                'state_or_region': 'Kerala',
                'name': 'Munnar & Alleppey',
                'description': 'Gods Own Country: emerald tea plantations, spice gardens, and tranquil backwaters luxury houseboat cruises.',
                'image_url': 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'MODERATE',
                'popularity_score': 96,
                'latitude': 9.4981,
                'longitude': 76.3388,
                'best_season': 'September - March',
                'avg_daily_cost': 3500.00
            },

            # === GLOBAL HUBS ===
            {
                'country': 'Japan',
                'state_or_region': 'Kanto',
                'name': 'Tokyo',
                'description': 'Futuristic metropolis blending skyscrapers, neon streets, ancient shrines, and world-class gastronomy.',
                'image_url': 'https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'LUXURY',
                'popularity_score': 98,
                'latitude': 35.6762,
                'longitude': 139.6503,
                'best_season': 'March - May & October - November',
                'avg_daily_cost': 12000.00
            },
            {
                'country': 'France',
                'state_or_region': 'Ile-de-France',
                'name': 'Paris',
                'description': 'The City of Light: Eiffel Tower, Louvre museum, chic cafes, and romantic Seine river cruises.',
                'image_url': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'LUXURY',
                'popularity_score': 99,
                'latitude': 48.8566,
                'longitude': 2.3522,
                'best_season': 'May - October',
                'avg_daily_cost': 16000.00
            },
            {
                'country': 'Indonesia',
                'state_or_region': 'Bali Province',
                'name': 'Bali',
                'description': 'Tropical paradise with emerald rice terraces, cliffside temples, surf beaches, and floral spa retreats.',
                'image_url': 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'BUDGET',
                'popularity_score': 97,
                'latitude': -8.4095,
                'longitude': 115.1889,
                'best_season': 'April - October',
                'avg_daily_cost': 5500.00
            },
            {
                'country': 'Switzerland',
                'state_or_region': 'Zurich Canton',
                'name': 'Zurich',
                'description': 'Picturesque Swiss alpine gateway on Lake Zurich with chocolate boutiques and mountain vistas.',
                'image_url': 'https://images.unsplash.com/photo-1515488764276-beab7607c1e6?w=1000&auto=format&fit=crop&q=80',
                'cost_index': 'LUXURY',
                'popularity_score': 91,
                'latitude': 47.3769,
                'longitude': 8.5417,
                'best_season': 'June - September & Winter',
                'avg_daily_cost': 18000.00
            }
        ]

        city_map = {}
        for cdata in cities_data:
            country_obj = country_map[cdata.pop('country')]
            city_obj, _ = City.objects.get_or_create(
                name=cdata['name'],
                defaults={'country': country_obj, **cdata}
            )
            city_obj.state_or_region = cdata.get('state_or_region', '')
            city_obj.save()
            city_map[city_obj.name] = city_obj

        self.stdout.write(self.style.SUCCESS(f"[OK] Created {len(city_map)} Destinations."))

        # 4. Create Activities Catalogue with INR pricing
        activities_data = [
            # Kashmir
            ('Srinagar', 'Sunset Shikara Ride on Dal Lake & Floating Market', 'RELAXATION', 'Glide across serene Dal Lake in a cushioned wooden shikara witnessing sunset over Zabarwan mountains.', 800.00, 2.0, 'https://images.unsplash.com/photo-1566837945700-30057527ade0?w=600&auto=format&fit=crop&q=80', 5.0, 'Boulevard Road, Dal Lake, Srinagar'),
            ('Srinagar', 'Mughal Gardens Tour: Shalimar & Nishat Bagh', 'SIGHTSEEING', 'Explore terraced Persian fountains, Chinar trees, and historic royal Mughal pavilions.', 400.00, 2.5, 'https://images.unsplash.com/photo-1598091383021-15ddea10925d?w=600&auto=format&fit=crop&q=80', 4.8, 'Nishat, Srinagar'),
            ('Gulmarg', 'Gulmarg Gondola Ride to Apharwat Peak (Phase 1 & 2)', 'ADVENTURE', 'Ride Asia highest cable car to 13,780 ft surrounded by snow slopes and Himalayan ranges.', 2000.00, 3.5, 'https://images.unsplash.com/photo-1595846519845-68e298c2edd8?w=600&auto=format&fit=crop&q=80', 4.9, 'Gondola Base, Gulmarg'),
            ('Pahalgam', 'Betaab Valley & Aru Valley Pony Trek', 'ADVENTURE', 'Trek along crystal-clear Lidder streams and lush green pine valleys named after Bollywood hits.', 1200.00, 3.0, 'https://images.unsplash.com/photo-1601000938259-9e92002320b2?w=600&auto=format&fit=crop&q=80', 4.9, 'Betaab Valley, Pahalgam'),

            # Himachal Pradesh
            ('Manali', 'Solang Valley Paragliding & Snow Adventure Sports', 'ADVENTURE', 'High-thrill tandem paragliding, zorbing, and quad biking overlooking the Pir Panjal mountains.', 2500.00, 3.0, 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=600&auto=format&fit=crop&q=80', 4.9, 'Solang Valley, Manali'),
            ('Manali', 'Rohtang Pass & Atal Tunnel Snow Excursion', 'ADVENTURE', 'Drive through the engineering marvel Atal Tunnel to 13,058 ft Rohtang Pass for breathtaking glaciers.', 3000.00, 6.0, 'https://images.unsplash.com/photo-1579618218290-24a26f63a778?w=600&auto=format&fit=crop&q=80', 4.9, 'Rohtang Pass Highway, Manali'),
            ('Shimla', 'Heritage Walk on Mall Road & Kalka-Shimla Toy Train', 'CULTURE', 'Explore colonial heritage, Gaiety Theatre, Christ Church, and ride the scenic narrow gauge toy train.', 600.00, 2.5, 'https://images.unsplash.com/photo-1597074866923-dc0589150358?w=600&auto=format&fit=crop&q=80', 4.8, 'The Ridge, Shimla'),
            ('Dharamshala & Bir Billing', 'World-Class Tandem Paragliding Flight in Bir', 'ADVENTURE', 'Take off from 8,000 ft at Billing and soar over Kangra tea valleys with certified pilots.', 3200.00, 2.0, 'https://images.unsplash.com/photo-1571401835393-8c5f35328320?w=600&auto=format&fit=crop&q=80', 5.0, 'Bir Billing, Himachal Pradesh'),

            # Gujarat
            ('Ahmedabad', 'Manek Chowk Night Food Trail & Heritage Walk', 'FOOD', 'Taste iconic Gwalior Dosa, maskabun, Jalebi-Fafda, and rabri in Ahmedabad bustling old city.', 500.00, 2.5, 'https://images.unsplash.com/photo-1609137144822-094ba470ec9e?w=600&auto=format&fit=crop&q=80', 4.9, 'Manek Chowk, Ahmedabad'),
            ('Ahmedabad', 'Sabarmati Ashram & Adalaj Stepwell Guided Tour', 'CULTURE', 'Experience Mahatma Gandhi serene residence and the architectural brilliance of the 5-story stepwell.', 400.00, 3.0, 'https://images.unsplash.com/photo-1588416936097-41850ab3d86d?w=600&auto=format&fit=crop&q=80', 4.8, 'Ashram Road, Ahmedabad'),
            ('Rann of Kutch', 'Rann Utsav Full Moon White Desert Safari', 'CULTURE', 'Witness infinite glistening white salt crystals under moonlight with live Gujarati folk music and camel safaris.', 1500.00, 4.0, 'https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=600&auto=format&fit=crop&q=80', 5.0, 'Dhordo Tent City, Kutch'),
            ('Gir National Park & Somnath', 'Open Jeep Safari for Asiatic Lions in Sasan Gir', 'ADVENTURE', 'Thrilling morning jungle safari through the natural habitat of wild Asiatic lions.', 4200.00, 3.5, 'https://images.unsplash.com/photo-1534177616072-ef7dc120449d?w=600&auto=format&fit=crop&q=80', 4.9, 'Sasan Gir Wildlife Sanctuary, Gujarat'),
            ('Statue of Unity (Kevadia)', 'Statue of Unity Viewing Gallery & Light Laser Show', 'SIGHTSEEING', 'Express high-speed elevator to the 153m chest level viewing gallery followed by high-tech laser show.', 1000.00, 3.0, 'https://images.unsplash.com/photo-1588416936097-41850ab3d86d?w=600&auto=format&fit=crop&q=80', 4.8, 'Kevadia Colony, Gujarat'),

            # Rajasthan, Ladakh & Global
            ('Jaipur & Udaipur', 'Amber Fort Elephant/Jeep Safari & City Palace', 'CULTURE', 'Grand Rajasthani royal palace tour, Sheesh Mahal mirror palace, and Lake Pichola boat ride.', 1800.00, 4.0, 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=600&auto=format&fit=crop&q=80', 4.9, 'Amer, Jaipur & Udaipur'),
            ('Leh Ladakh', 'Pangong Tso Lake & Nubra Valley Camel Safari', 'ADVENTURE', 'Scenic drive over Chang La Pass to the color-shifting blue Pangong Lake and Hunder sand dunes.', 4500.00, 6.0, 'https://images.unsplash.com/photo-1581793745862-99fde7fa73d2?w=600&auto=format&fit=crop&q=80', 5.0, 'Pangong Tso, Ladakh'),
            ('Munnar & Alleppey', 'Private Luxury Houseboat Cruise on Alleppey Backwaters', 'RELAXATION', 'Day cruise through palm-fringed canals with traditional Kerala sadya lunch cooked onboard.', 3500.00, 5.0, 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=600&auto=format&fit=crop&q=80', 4.9, 'Finishing Point, Alleppey'),
            ('Tokyo', 'Shibuya Crossing & Izakaya Ramen Tour', 'FOOD', 'Taste authentic ramen and yakitori around Shibuya scramble crossing.', 3800.00, 3.0, 'https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=600&auto=format&fit=crop&q=80', 4.9, 'Shibuya, Tokyo'),
            ('Paris', 'Sunset Eiffel Tower & Seine Cruise', 'SIGHTSEEING', 'Ascend the Eiffel Tower and cruise along the Seine River.', 6200.00, 3.0, 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=600&auto=format&fit=crop&q=80', 4.9, 'Paris, France'),
            ('Bali', 'Ubud Rice Terraces & Volcano Trek', 'ADVENTURE', 'Trek through emerald rice terraces and Mount Batur sunrise crater.', 3200.00, 4.0, 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=600&auto=format&fit=crop&q=80', 4.8, 'Ubud, Bali'),
        ]

        activity_map = {}
        for cname, aname, cat, desc, cost, dur, img, rat, loc in activities_data:
            if cname in city_map:
                cobj = city_map[cname]
                act_obj, _ = Activity.objects.get_or_create(
                    city=cobj,
                    name=aname,
                    defaults={
                        'category': cat,
                        'description': desc,
                        'estimated_cost': cost,
                        'duration_hours': dur,
                        'image_url': img,
                        'rating': rat,
                        'location_address': loc,
                        'is_featured': True
                    }
                )
                activity_map[aname] = act_obj

        self.stdout.write(self.style.SUCCESS(f"[OK] Created {len(activity_map)} Activities."))

        # 5. Create Wishlists
        WishlistDestination.objects.get_or_create(user=traveler, city=city_map['Srinagar'])
        WishlistDestination.objects.get_or_create(user=traveler, city=city_map['Manali'])
        WishlistDestination.objects.get_or_create(user=traveler, city=city_map['Rann of Kutch'])
        WishlistDestination.objects.get_or_create(user=sarah, city=city_map['Gulmarg'])
        WishlistDestination.objects.get_or_create(user=sarah, city=city_map['Ahmedabad'])

        # 6. Create Multi-City Indian Itineraries with INR
        # Trip 1: Aarav's Kashmir & Himachal Himalayan Odyssey
        start_1 = date.today() + timedelta(days=7)
        end_1 = start_1 + timedelta(days=7)
        trip_1, _ = Trip.objects.get_or_create(
            user=traveler,
            title="Magical Kashmir & Himachal: Srinagar, Gulmarg & Manali",
            defaults={
                'description': "An 8-day Himalayan dream trip combining Dal Lake shikaras, Gulmarg snowy peaks, and Solang Valley mountain adventures in Manali.",
                'start_date': start_1,
                'end_date': end_1,
                'estimated_budget': 48000.00,
                'currency': 'INR',
                'travel_style': 'ADVENTURE',
                'is_public': True,
                'status': 'UPCOMING',
                'cover_image_url': 'https://images.unsplash.com/photo-1566837945700-30057527ade0?w=1200&auto=format&fit=crop&q=80'
            }
        )

        stop_srinagar, _ = TripStop.objects.get_or_create(
            trip=trip_1,
            city=city_map['Srinagar'],
            defaults={
                'arrival_date': start_1,
                'departure_date': start_1 + timedelta(days=3),
                'stop_order': 1,
                'accommodation_name': 'Royal Dal Lake Luxury Houseboat',
                'stay_cost': 9500.00,
                'transport_to_stop_type': 'FLIGHT',
                'transport_cost': 7500.00,
                'notes': 'Flight to Srinagar Airport -> Direct pickup to Houseboat at Ghat No. 7.'
            }
        )

        stop_gulmarg, _ = TripStop.objects.get_or_create(
            trip=trip_1,
            city=city_map['Gulmarg'],
            defaults={
                'arrival_date': start_1 + timedelta(days=3),
                'departure_date': start_1 + timedelta(days=5),
                'stop_order': 2,
                'accommodation_name': 'Khyber Himalayan Resort & Spa',
                'stay_cost': 8000.00,
                'transport_to_stop_type': 'CAR',
                'transport_cost': 2500.00,
                'notes': 'Private cab via Tangmarg to Gulmarg meadow.'
            }
        )

        stop_manali, _ = TripStop.objects.get_or_create(
            trip=trip_1,
            city=city_map['Manali'],
            defaults={
                'arrival_date': start_1 + timedelta(days=5),
                'departure_date': end_1,
                'stop_order': 3,
                'accommodation_name': 'Old Manali Apple Orchard Cottage',
                'stay_cost': 6500.00,
                'transport_to_stop_type': 'BUS',
                'transport_cost': 3200.00,
                'notes': 'Volvo bus transfer through scenic mountain tunnels.'
            }
        )

        # Activities for Trip 1
        ScheduledActivity.objects.get_or_create(
            stop=stop_srinagar,
            title="Sunset Shikara Ride on Dal Lake & Floating Market",
            defaults={
                'activity': activity_map.get('Sunset Shikara Ride on Dal Lake & Floating Market'),
                'category': 'RELAXATION',
                'scheduled_date': start_1,
                'start_time': '16:30:00',
                'duration_minutes': 120,
                'cost': 800.00,
                'location': 'Dal Lake, Srinagar'
            }
        )
        ScheduledActivity.objects.get_or_create(
            stop=stop_srinagar,
            title="Mughal Gardens Tour: Shalimar & Nishat Bagh",
            defaults={
                'activity': activity_map.get('Mughal Gardens Tour: Shalimar & Nishat Bagh'),
                'category': 'SIGHTSEEING',
                'scheduled_date': start_1 + timedelta(days=1),
                'start_time': '10:00:00',
                'duration_minutes': 150,
                'cost': 400.00,
                'location': 'Nishat, Srinagar'
            }
        )
        ScheduledActivity.objects.get_or_create(
            stop=stop_gulmarg,
            title="Gulmarg Gondola Ride to Apharwat Peak (Phase 1 & 2)",
            defaults={
                'activity': activity_map.get('Gulmarg Gondola Ride to Apharwat Peak (Phase 1 & 2)'),
                'category': 'ADVENTURE',
                'scheduled_date': start_1 + timedelta(days=3),
                'start_time': '09:00:00',
                'duration_minutes': 210,
                'cost': 2000.00,
                'location': 'Gulmarg, Kashmir'
            }
        )
        ScheduledActivity.objects.get_or_create(
            stop=stop_manali,
            title="Solang Valley Paragliding & Snow Adventure Sports",
            defaults={
                'activity': activity_map.get('Solang Valley Paragliding & Snow Adventure Sports'),
                'category': 'ADVENTURE',
                'scheduled_date': start_1 + timedelta(days=6),
                'start_time': '10:30:00',
                'duration_minutes': 180,
                'cost': 2500.00,
                'location': 'Solang Valley, Manali'
            }
        )

        # Logged Expenses for Trip 1
        TripExpense.objects.get_or_create(
            trip=trip_1,
            title="Traditional Kashmiri Wazwan Feast",
            defaults={'category': 'MEAL', 'amount': 1800.00, 'expense_date': start_1}
        )
        TripExpense.objects.get_or_create(
            trip=trip_1,
            title="Kashmiri Pashmina Shawl & Saffron",
            defaults={'category': 'SHOPPING', 'amount': 3500.00, 'expense_date': start_1 + timedelta(days=2)}
        )

        TripReview.objects.get_or_create(
            trip=trip_1,
            user=sarah,
            defaults={
                'rating': 5,
                'title': 'Breathtaking mountain route & perfect budget!',
                'comment': 'Kashmir in houseboats followed by Gulmarg snow gondola was pure bliss. Very accurate INR budget breakdown!'
            }
        )
        TripLike.objects.get_or_create(trip=trip_1, user=sarah)
        TripLike.objects.get_or_create(trip=trip_1, user=rohit)

        # Trip 2: Rohit's Vibrant Gujarat Cultural Expedition
        start_2 = date.today() + timedelta(days=20)
        end_2 = start_2 + timedelta(days=6)
        trip_2, _ = Trip.objects.get_or_create(
            user=rohit,
            title="Vibrant Gujarat Heritage & Rann of Kutch White Desert",
            defaults={
                'description': "Explore Ahmedabad UNESCO heritage and Manek Chowk night foods, the full-moon White Desert at Rann of Kutch, and Asiatic Lions at Sasan Gir.",
                'start_date': start_2,
                'end_date': end_2,
                'estimated_budget': 36000.00,
                'currency': 'INR',
                'travel_style': 'FAMILY',
                'is_public': True,
                'status': 'PLANNING',
                'cover_image_url': 'https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200&auto=format&fit=crop&q=80'
            }
        )

        stop_ahmedabad, _ = TripStop.objects.get_or_create(
            trip=trip_2,
            city=city_map['Ahmedabad'],
            defaults={
                'arrival_date': start_2,
                'departure_date': start_2 + timedelta(days=2),
                'stop_order': 1,
                'accommodation_name': 'House of MG Heritage Hotel',
                'stay_cost': 5500.00,
                'transport_to_stop_type': 'TRAIN',
                'transport_cost': 1800.00,
            }
        )

        stop_kutch, _ = TripStop.objects.get_or_create(
            trip=trip_2,
            city=city_map['Rann of Kutch'],
            defaults={
                'arrival_date': start_2 + timedelta(days=2),
                'departure_date': start_2 + timedelta(days=5),
                'stop_order': 2,
                'accommodation_name': 'Dhordo White Rann Utsav Luxury Tent',
                'stay_cost': 11000.00,
                'transport_to_stop_type': 'CAR',
                'transport_cost': 3500.00,
            }
        )

        ScheduledActivity.objects.get_or_create(
            stop=stop_ahmedabad,
            title="Manek Chowk Night Food Trail & Heritage Walk",
            defaults={
                'activity': activity_map.get('Manek Chowk Night Food Trail & Heritage Walk'),
                'category': 'FOOD',
                'scheduled_date': start_2,
                'start_time': '20:00:00',
                'duration_minutes': 150,
                'cost': 500.00,
            }
        )

        ScheduledActivity.objects.get_or_create(
            stop=stop_kutch,
            title="Rann Utsav Full Moon White Desert Safari",
            defaults={
                'activity': activity_map.get('Rann Utsav Full Moon White Desert Safari'),
                'category': 'CULTURE',
                'scheduled_date': start_2 + timedelta(days=3),
                'start_time': '17:30:00',
                'duration_minutes': 240,
                'cost': 1500.00,
            }
        )

        TripLike.objects.get_or_create(trip=trip_2, user=traveler)
        TripReview.objects.get_or_create(
            trip=trip_2,
            user=traveler,
            defaults={
                'rating': 5,
                'title': 'Rann of Kutch is unforgettable!',
                'comment': 'The white salt desert at sunset and Kathiyawadi thali in Ahmedabad were out of this world. Highly recommended!'
            }
        )

        # 7. Live Activity Logs
        ActivityLog.objects.create(
            user=traveler,
            event_type='TRIP_CREATE',
            title="Aarav mapped 'Magical Kashmir & Himachal: Srinagar, Gulmarg & Manali'",
            description="Aarav created an 8-day Himalayan multi-city itinerary budgeted in INR (₹48,000).",
            reference_url=f"/trips/share/{trip_1.share_slug}/",
            icon="fa-mountain"
        )
        ActivityLog.objects.create(
            user=rohit,
            event_type='TRIP_CREATE',
            title="Rohit published 'Vibrant Gujarat Heritage & Rann of Kutch'",
            description="Rohit shared a 7-day family itinerary exploring Ahmedabad, Kutch white desert, and Gir lions.",
            reference_url=f"/trips/share/{trip_2.share_slug}/",
            icon="fa-landmark"
        )
        ActivityLog.objects.create(
            user=sarah,
            event_type='DESTINATION_EXPLORE',
            title="Sarah wishlisted Gulmarg, Kashmir",
            description="Saved scenic snow destination Gulmarg, Kashmir to travel bucket list.",
            icon="fa-heart"
        )
        ActivityLog.objects.create(
            user=traveler,
            event_type='TRIP_CLONE',
            title="Aarav cloned 'Vibrant Gujarat Heritage'",
            description="Aarav copied Rohit's Kutch & Ahmedabad plan to their account.",
            reference_url=f"/trips/share/{trip_2.share_slug}/",
            icon="fa-copy"
        )

        self.stdout.write(self.style.SUCCESS("GlobeTrotter enhanced database seeding completed successfully!"))
