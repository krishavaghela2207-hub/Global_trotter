from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from travel_planner.models import (
    UserProfile, Region, Country, City, ActivityCategory,
    Activity, Trip, TripStop, ItineraryItem, TripExpense,
    TripLike, TripComment, SavedDestination
)

class Command(BaseCommand):
    help = 'Seeds initial realistic travel data for GlobeTrotter'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("[*] Seeding GlobeTrotter database..."))

        # 1. Create Superuser and Demo Users
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@globetrotter.io',
                'first_name': 'Global',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()
        UserProfile.objects.filter(user=admin_user).update(
            bio="Lead Platform Administrator for GlobeTrotter ecosystem.",
            city="San Francisco",
            country="United States",
            avatar_url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=300&auto=format&fit=crop&q=80"
        )

        alex, _ = User.objects.get_or_create(
            username='alex_traveler',
            defaults={
                'email': 'alex.rivera@example.com',
                'first_name': 'Alex',
                'last_name': 'Rivera',
            }
        )
        alex.set_password('alex123')
        alex.save()
        UserProfile.objects.filter(user=alex).update(
            bio="Adventure seeker & travel photographer. 28 countries and counting. Passionate about culinary arts and cultural deep-dives.",
            phone_number="+1 (555) 234-8901",
            city="New York",
            country="United States",
            avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&auto=format&fit=crop&q=80",
            currency_preference="USD",
            language_preference="en"
        )

        sophia, _ = User.objects.get_or_create(
            username='sophia_chen',
            defaults={
                'email': 'sophia.chen@example.com',
                'first_name': 'Sophia',
                'last_name': 'Chen',
            }
        )
        sophia.set_password('sophia123')
        sophia.save()
        UserProfile.objects.filter(user=sophia).update(
            bio="Architect and solo globetrotter. Exploring historic landmarks, modern urban design, and alpine landscapes.",
            phone_number="+44 20 7946 0192",
            city="London",
            country="United Kingdom",
            avatar_url="https://images.unsplash.com/photo-1517841905240-472988babdf9?w=300&auto=format&fit=crop&q=80",
            currency_preference="EUR",
            language_preference="en"
        )

        marcus, _ = User.objects.get_or_create(
            username='marcus_vance',
            defaults={
                'email': 'marcus.vance@example.com',
                'first_name': 'Marcus',
                'last_name': 'Vance',
            }
        )
        marcus.set_password('marcus123')
        marcus.save()
        UserProfile.objects.filter(user=marcus).update(
            bio="High-altitude trekking enthusiast, scuba diver, and slow travel advocate.",
            phone_number="+61 2 9876 5432",
            city="Sydney",
            country="Australia",
            avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&auto=format&fit=crop&q=80",
            currency_preference="USD"
        )

        # 2. Activity Categories
        categories_data = [
            {'name': 'Sightseeing & Landmarks', 'slug': 'sightseeing', 'icon': 'camera', 'color': '#3B82F6'},
            {'name': 'Food & Culinary Tours', 'slug': 'food-dining', 'icon': 'utensils', 'color': '#F59E0B'},
            {'name': 'Adventure & Nature', 'slug': 'adventure', 'icon': 'compass', 'color': '#10B981'},
            {'name': 'Culture & History', 'slug': 'culture', 'icon': 'landmark', 'color': '#8B5CF6'},
            {'name': 'Relaxation & Wellness', 'slug': 'relaxation', 'icon': 'sparkles', 'color': '#EC4899'},
            {'name': 'Nightlife & Shows', 'slug': 'nightlife', 'icon': 'moon', 'color': '#6366F1'},
        ]
        cat_map = {}
        for c in categories_data:
            cat_obj, _ = ActivityCategory.objects.get_or_create(
                slug=c['slug'],
                defaults={'name': c['name'], 'icon': c['icon'], 'color': c['color']}
            )
            cat_map[c['slug']] = cat_obj

        # 3. Regions & Countries
        regions_data = [
            {'name': 'Europe', 'code': 'EUR', 'desc': 'Timeless architecture, culinary traditions, and diverse romantic landscapes.', 'img': 'https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=800&auto=format&fit=crop&q=80'},
            {'name': 'Asia & Pacific', 'code': 'ASIA', 'desc': 'Vibrant megacities, ancient shrines, pristine islands, and rich heritage.', 'img': 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800&auto=format&fit=crop&q=80'},
            {'name': 'North America', 'code': 'NA', 'desc': 'Iconic skylines, national parks, entertainment hubs, and coastal vistas.', 'img': 'https://images.unsplash.com/photo-1506146332389-18140dc7b2fb?w=800&auto=format&fit=crop&q=80'},
            {'name': 'Africa & Middle East', 'code': 'AFR-ME', 'desc': 'Ancient wonders, safari wildlife, desert dunes, and golden skylines.', 'img': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800&auto=format&fit=crop&q=80'},
            {'name': 'South America', 'code': 'SA', 'desc': 'Rainforests, carnival rhythms, Andean peaks, and vibrant coastal cities.', 'img': 'https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=800&auto=format&fit=crop&q=80'},
            {'name': 'Oceania', 'code': 'OCE', 'desc': 'Coral reefs, coastal lifestyle, harbor panoramas, and sunlit wilderness.', 'img': 'https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=800&auto=format&fit=crop&q=80'}
        ]
        reg_map = {}
        for r in regions_data:
            reg_obj, _ = Region.objects.get_or_create(
                code=r['code'],
                defaults={'name': r['name'], 'description': r['desc'], 'image_url': r['img']}
            )
            reg_map[r['code']] = reg_obj

        countries_data = [
            {'name': 'France', 'code': 'FR', 'reg': 'EUR', 'curr': 'EUR', 'flag': '🇫🇷'},
            {'name': 'Japan', 'code': 'JP', 'reg': 'ASIA', 'curr': 'JPY', 'flag': '🇯🇵'},
            {'name': 'Italy', 'code': 'IT', 'reg': 'EUR', 'curr': 'EUR', 'flag': '🇮🇹'},
            {'name': 'United States', 'code': 'US', 'reg': 'NA', 'curr': 'USD', 'flag': '🇺🇸'},
            {'name': 'Indonesia', 'code': 'ID', 'reg': 'ASIA', 'curr': 'IDR', 'flag': '🇮🇩'},
            {'name': 'Spain', 'code': 'ES', 'reg': 'EUR', 'curr': 'EUR', 'flag': '🇪🇸'},
            {'name': 'United Kingdom', 'code': 'GB', 'reg': 'EUR', 'curr': 'GBP', 'flag': '🇬🇧'},
            {'name': 'South Africa', 'code': 'ZA', 'reg': 'AFR-ME', 'curr': 'ZAR', 'flag': '🇿🇦'},
            {'name': 'Australia', 'code': 'AU', 'reg': 'OCE', 'curr': 'AUD', 'flag': '🇦🇺'},
            {'name': 'United Arab Emirates', 'code': 'AE', 'reg': 'AFR-ME', 'curr': 'AED', 'flag': '🇦🇪'},
            {'name': 'Egypt', 'code': 'EG', 'reg': 'AFR-ME', 'curr': 'EGP', 'flag': '🇪🇬'},
            {'name': 'Thailand', 'code': 'TH', 'reg': 'ASIA', 'curr': 'THB', 'flag': '🇹🇭'},
            {'name': 'Brazil', 'code': 'BR', 'reg': 'SA', 'curr': 'BRL', 'flag': '🇧🇷'},
            {'name': 'Greece', 'code': 'GR', 'reg': 'EUR', 'curr': 'EUR', 'flag': '🇬🇷'},
            {'name': 'Switzerland', 'code': 'CH', 'reg': 'EUR', 'curr': 'CHF', 'flag': '🇨🇭'},
        ]
        country_map = {}
        for c in countries_data:
            country_obj, _ = Country.objects.get_or_create(
                code=c['code'],
                defaults={
                    'name': c['name'],
                    'region': reg_map[c['reg']],
                    'currency': c['curr'],
                    'flag_emoji': c['flag']
                }
            )
            country_map[c['name']] = country_obj

        # 4. Cities
        cities_data = [
            {
                'name': 'Paris', 'country': 'France', 'region': 'EUR', 'cost': '$$$', 'pop': 98.5,
                'desc': 'The City of Light captivates with the Eiffel Tower, world-renowned Louvre museum, boulevard cafes, and romantic Seine river cruises.',
                'img': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&auto=format&fit=crop&q=80',
                'best_time': 'April to October', 'avg_cost': 185.00, 'climate': 'Temperate Oceanic',
                'lat': 48.8566, 'lng': 2.3522
            },
            {
                'name': 'Tokyo', 'country': 'Japan', 'region': 'ASIA', 'cost': '$$$', 'pop': 99.0,
                'desc': 'A breathtaking fusion of ultramodern neon skyscrapers and serene historic temples, famous for world-class sushi, anime hubs, and bullet trains.',
                'img': 'https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=800&auto=format&fit=crop&q=80',
                'best_time': 'March to May & Sept to Nov', 'avg_cost': 195.00, 'climate': 'Humid Subtropical',
                'lat': 35.6762, 'lng': 139.6503
            },
            {
                'name': 'Rome', 'country': 'Italy', 'region': 'EUR', 'cost': '$$', 'pop': 95.0,
                'desc': 'The Eternal City features 3,000 years of globally influential art, architecture, ancient Colosseum ruins, and exquisite handmade pasta.',
                'img': 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800&auto=format&fit=crop&q=80',
                'best_time': 'April to June & Sept to Oct', 'avg_cost': 140.00, 'climate': 'Mediterranean',
                'lat': 41.9028, 'lng': 12.4964
            },
            {
                'name': 'New York City', 'country': 'United States', 'region': 'NA', 'cost': '$$$', 'pop': 97.0,
                'desc': 'The city that never sleeps offers Broadway theater, Central Park strolls, dazzling Times Square lights, and the iconic Manhattan skyline.',
                'img': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800&auto=format&fit=crop&q=80',
                'best_time': 'April to June & Sept to Nov', 'avg_cost': 225.00, 'climate': 'Humid Continental',
                'lat': 40.7128, 'lng': -74.0060
            },
            {
                'name': 'Bali', 'country': 'Indonesia', 'region': 'ASIA', 'cost': '$', 'pop': 94.5,
                'desc': 'Island of the Gods boasting lush terraced rice paddies, serene coastal beaches, cliffside Hindu temples, and rejuvenating holistic spas.',
                'img': 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800&auto=format&fit=crop&q=80',
                'best_time': 'April to October', 'avg_cost': 65.00, 'climate': 'Tropical',
                'lat': -8.4095, 'lng': 115.1889
            },
            {
                'name': 'Barcelona', 'country': 'Spain', 'region': 'EUR', 'cost': '$$', 'pop': 93.5,
                'desc': 'Catalan masterpiece known for Gaudí’s Sagrada Família, sun-drenched Mediterranean beaches, tapas bars, and lively Gothic Quarter alleys.',
                'img': 'https://images.unsplash.com/photo-1583422409516-2895a77efded?w=800&auto=format&fit=crop&q=80',
                'best_time': 'May to June & Sept to Oct', 'avg_cost': 130.00, 'climate': 'Mediterranean',
                'lat': 41.3851, 'lng': 2.1734
            },
            {
                'name': 'Kyoto', 'country': 'Japan', 'region': 'ASIA', 'cost': '$$', 'pop': 92.0,
                'desc': 'The cultural heart of Japan with thousands of classical Buddhist temples, gardens, imperial palaces, Shinto shrines, and traditional geisha districts.',
                'img': 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800&auto=format&fit=crop&q=80',
                'best_time': 'March to May & Oct to Nov', 'avg_cost': 145.00, 'climate': 'Humid Subtropical',
                'lat': 35.0116, 'lng': 135.7681
            },
            {
                'name': 'Cape Town', 'country': 'South Africa', 'region': 'AFR-ME', 'cost': '$', 'pop': 89.0,
                'desc': 'Where dramatic Table Mountain meets turquoise oceans, featuring penguin colonies, scenic vineyards, and coastal cliffside drives.',
                'img': 'https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=800&auto=format&fit=crop&q=80',
                'best_time': 'November to April', 'avg_cost': 85.00, 'climate': 'Mediterranean',
                'lat': -33.9249, 'lng': 18.4241
            },
            {
                'name': 'Dubai', 'country': 'United Arab Emirates', 'region': 'AFR-ME', 'cost': '$$$', 'pop': 96.0,
                'desc': 'Futuristic oasis of luxury featuring the soaring Burj Khalifa, palm-shaped artificial islands, gold souks, and desert dune safaris.',
                'img': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800&auto=format&fit=crop&q=80',
                'best_time': 'November to March', 'avg_cost': 210.00, 'climate': 'Desert',
                'lat': 25.2048, 'lng': 55.2708
            },
            {
                'name': 'Sydney', 'country': 'Australia', 'region': 'OCE', 'cost': '$$$', 'pop': 91.5,
                'desc': 'Famous for its iconic Opera House sails, Sydney Harbour Bridge, world-class Bondi Beach surfing, and sun-soaked coastal walks.',
                'img': 'https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=800&auto=format&fit=crop&q=80',
                'best_time': 'September to November & March to May', 'avg_cost': 175.00, 'climate': 'Temperate Maritime',
                'lat': -33.8688, 'lng': 151.2093
            },
            {
                'name': 'London', 'country': 'United Kingdom', 'region': 'EUR', 'cost': '$$$', 'pop': 97.5,
                'desc': 'Historic royalty meets vibrant innovation with Big Ben, the Tower of London, West End theaters, and bustling international food markets.',
                'img': 'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&auto=format&fit=crop&q=80',
                'best_time': 'May to September', 'avg_cost': 195.00, 'climate': 'Temperate Oceanic',
                'lat': 51.5074, 'lng': -0.1278
            },
            {
                'name': 'Santorini', 'country': 'Greece', 'region': 'EUR', 'cost': '$$$', 'pop': 93.0,
                'desc': 'Whitewashed cubiform cliff houses, cobalt blue domes, volcanic caldera views, and world-famous golden sunsets over the Aegean Sea.',
                'img': 'https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=800&auto=format&fit=crop&q=80',
                'best_time': 'Late April to early November', 'avg_cost': 170.00, 'climate': 'Mediterranean',
                'lat': 36.3932, 'lng': 25.4615
            },
            {
                'name': 'Bangkok', 'country': 'Thailand', 'region': 'ASIA', 'cost': '$', 'pop': 92.5,
                'desc': 'A vibrant metropolis of ornate riverside shrines, buzzing tuk-tuks, night markets, and world-famous street food stalls.',
                'img': 'https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=800&auto=format&fit=crop&q=80',
                'best_time': 'November to February', 'avg_cost': 60.00, 'climate': 'Tropical Savanna',
                'lat': 13.7563, 'lng': 100.5018
            },
            {
                'name': 'Rio de Janeiro', 'country': 'Brazil', 'region': 'SA', 'cost': '$$', 'pop': 87.5,
                'desc': 'Marvelous city with Christ the Redeemer atop Corcovado, Sugarloaf Mountain cable cars, Copacabana sands, and samba music in the air.',
                'img': 'https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=800&auto=format&fit=crop&q=80',
                'best_time': 'December to March', 'avg_cost': 90.00, 'climate': 'Tropical',
                'lat': -22.9068, 'lng': -43.1729
            },
            {
                'name': 'Cairo', 'country': 'Egypt', 'region': 'AFR-ME', 'cost': '$', 'pop': 88.0,
                'desc': 'Gateway to antiquity featuring the Great Pyramids of Giza, the enigmatic Sphinx, bustling Khan el-Khalili bazaar, and the mighty Nile River.',
                'img': 'https://images.unsplash.com/photo-1572252009286-268acec5ca0a?w=800&auto=format&fit=crop&q=80',
                'best_time': 'October to April', 'avg_cost': 55.00, 'climate': 'Desert',
                'lat': 30.0444, 'lng': 31.2357
            },
            {
                'name': 'Zurich', 'country': 'Switzerland', 'region': 'EUR', 'cost': '$$$', 'pop': 90.0,
                'desc': 'Pristine lakeside city framed by snow-capped Alps, picturesque Old Town streets, premium Swiss chocolatiers, and crystal mountain waters.',
                'img': 'https://images.unsplash.com/photo-1515488764276-beab7607c1e6?w=800&auto=format&fit=crop&q=80',
                'best_time': 'June to August & Dec to Feb', 'avg_cost': 240.00, 'climate': 'Continental',
                'lat': 47.3769, 'lng': 8.5417
            }
        ]

        city_map = {}
        for c in cities_data:
            city_obj, _ = City.objects.get_or_create(
                name=c['name'],
                country=country_map[c['country']],
                defaults={
                    'region': reg_map[c['region']],
                    'cost_index': c['cost'],
                    'popularity_score': c['pop'],
                    'description': c['desc'],
                    'image_url': c['img'],
                    'best_time_to_visit': c['best_time'],
                    'avg_daily_cost': Decimal(str(c['avg_cost'])),
                    'climate_tag': c['climate'],
                    'latitude': c['lat'],
                    'longitude': c['lng'],
                }
            )
            city_map[c['name']] = city_obj

        # 5. Rich Curated Activities
        activities_data = [
            # Paris
            {'city': 'Paris', 'cat': 'sightseeing', 'title': 'Eiffel Tower Summit & Champagne', 'cost': 45.00, 'dur': 2.5, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1543349689-9a4d426bee8e?w=800&auto=format&fit=crop&q=80', 'loc': 'Champ de Mars, 7th Arrondissement'},
            {'city': 'Paris', 'cat': 'culture', 'title': 'Louvre Masterpieces Guided Tour', 'cost': 65.00, 'dur': 3.0, 'rating': 4.8, 'img': 'https://images.unsplash.com/photo-1565099824688-e93eb20fe622?w=800&auto=format&fit=crop&q=80', 'loc': 'Musée du Louvre, Rue de Rivoli'},
            {'city': 'Paris', 'cat': 'food-dining', 'title': 'Montmartre Gourmet Food & Wine Walk', 'cost': 85.00, 'dur': 3.5, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800&auto=format&fit=crop&q=80', 'loc': 'Place des Abbesses, Montmartre'},
            {'city': 'Paris', 'cat': 'relaxation', 'title': 'Sunset Seine River Bateaux Mouches', 'cost': 35.00, 'dur': 1.5, 'rating': 4.7, 'img': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&auto=format&fit=crop&q=80', 'loc': 'Pont Neuf Pier'},

            # Tokyo
            {'city': 'Tokyo', 'cat': 'sightseeing', 'title': 'Shibuya Sky & Scramble Crossing', 'cost': 22.00, 'dur': 2.0, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1542051841857-5f90071e7989?w=800&auto=format&fit=crop&q=80', 'loc': 'Shibuya Scramble Square'},
            {'city': 'Tokyo', 'cat': 'food-dining', 'title': 'Tsukiji Outer Market Tasting Tour', 'cost': 70.00, 'dur': 3.0, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=800&auto=format&fit=crop&q=80', 'loc': 'Tsukiji, Chuo City'},
            {'city': 'Tokyo', 'cat': 'culture', 'title': 'Senso-ji Asakusa Shrine & Kimono Experience', 'cost': 40.00, 'dur': 3.0, 'rating': 4.8, 'img': 'https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=800&auto=format&fit=crop&q=80', 'loc': 'Asakusa, Taito City'},
            {'city': 'Tokyo', 'cat': 'adventure', 'title': 'Akihabara Go-Kart City Safari', 'cost': 95.00, 'dur': 2.0, 'rating': 4.7, 'img': 'https://images.unsplash.com/photo-1536098561742-ca998e48cbcc?w=800&auto=format&fit=crop&q=80', 'loc': 'Akihabara Tech District'},

            # Rome
            {'city': 'Rome', 'cat': 'culture', 'title': 'Colosseum & Roman Forum VIP Access', 'cost': 55.00, 'dur': 3.0, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800&auto=format&fit=crop&q=80', 'loc': 'Piazza del Colosseo'},
            {'city': 'Rome', 'cat': 'food-dining', 'title': 'Trastevere Artisanal Pasta & Gelato Masterclass', 'cost': 75.00, 'dur': 3.5, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=800&auto=format&fit=crop&q=80', 'loc': 'Piazza Santa Maria in Trastevere'},
            {'city': 'Rome', 'cat': 'sightseeing', 'title': 'Vatican Museums & Sistine Chapel Tour', 'cost': 60.00, 'dur': 3.5, 'rating': 4.8, 'img': 'https://images.unsplash.com/photo-1531572753322-ad063cecc140?w=800&auto=format&fit=crop&q=80', 'loc': 'Vatican City'},

            # New York
            {'city': 'New York City', 'cat': 'sightseeing', 'title': 'Summit One Vanderbilt Glass Skydeck', 'cost': 48.00, 'dur': 2.0, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800&auto=format&fit=crop&q=80', 'loc': '45 E 42nd St, Midtown'},
            {'city': 'New York City', 'cat': 'nightlife', 'title': 'Broadway Musical Premium Orchestra Seats', 'cost': 140.00, 'dur': 3.0, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800&auto=format&fit=crop&q=80', 'loc': 'Broadway Theater District'},
            {'city': 'New York City', 'cat': 'food-dining', 'title': 'Chelsea Market & High Line Gastronomy Crawl', 'cost': 65.00, 'dur': 2.5, 'rating': 4.8, 'img': 'https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=800&auto=format&fit=crop&q=80', 'loc': '75 9th Ave, Chelsea'},

            # Bali
            {'city': 'Bali', 'cat': 'adventure', 'title': 'Mount Batur Sunrise Volcano Trek & Hot Springs', 'cost': 45.00, 'dur': 6.0, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800&auto=format&fit=crop&q=80', 'loc': 'Kintamani, Bangli'},
            {'city': 'Bali', 'cat': 'relaxation', 'title': 'Ubud Traditional Balinese Spa & Flower Bath', 'cost': 35.00, 'dur': 2.5, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=800&auto=format&fit=crop&q=80', 'loc': 'Jalan Raya Ubud'},
            {'city': 'Bali', 'cat': 'culture', 'title': 'Tanah Lot & Uluwatu Kecak Fire Dance at Sunset', 'cost': 30.00, 'dur': 4.0, 'rating': 4.8, 'img': 'https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?w=800&auto=format&fit=crop&q=80', 'loc': 'Uluwatu Cliff Temple'},

            # Barcelona
            {'city': 'Barcelona', 'cat': 'culture', 'title': 'Sagrada Família Towers & Crypt Fast-Track', 'cost': 40.00, 'dur': 2.5, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1583422409516-2895a77efded?w=800&auto=format&fit=crop&q=80', 'loc': 'Carrer de Mallorca, 401'},
            {'city': 'Barcelona', 'cat': 'food-dining', 'title': 'El Born Tapas, Jamón & Sangria Workshop', 'cost': 55.00, 'dur': 3.0, 'rating': 4.8, 'img': 'https://images.unsplash.com/photo-1515443961218-a51367888e4b?w=800&auto=format&fit=crop&q=80', 'loc': 'Plaça de Santa Maria'},
            {'city': 'Barcelona', 'cat': 'sightseeing', 'title': 'Park Güell Monumental Zone Exploration', 'cost': 18.00, 'dur': 2.0, 'rating': 4.7, 'img': 'https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=800&auto=format&fit=crop&q=80', 'loc': 'Gràcia District'},

            # Kyoto
            {'city': 'Kyoto', 'cat': 'sightseeing', 'title': 'Fushimi Inari Thousand Torii Shrine Morning Walk', 'cost': 15.00, 'dur': 3.0, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800&auto=format&fit=crop&q=80', 'loc': 'Fushimi-ku'},
            {'city': 'Kyoto', 'cat': 'culture', 'title': 'Traditional Tea Ceremony & Zen Garden Meditation', 'cost': 50.00, 'dur': 2.0, 'rating': 4.8, 'img': 'https://images.unsplash.com/photo-1528164344705-475426879c0d?w=800&auto=format&fit=crop&q=80', 'loc': 'Higashiyama Ward'},
            {'city': 'Kyoto', 'cat': 'adventure', 'title': 'Arashiyama Bamboo Grove & River Boat Ride', 'cost': 35.00, 'dur': 3.5, 'rating': 4.8, 'img': 'https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=800&auto=format&fit=crop&q=80', 'loc': 'Arashiyama, Ukyo Ward'},

            # Dubai
            {'city': 'Dubai', 'cat': 'sightseeing', 'title': 'Burj Khalifa 148th Floor At the Top SKY', 'cost': 95.00, 'dur': 2.0, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800&auto=format&fit=crop&q=80', 'loc': 'Downtown Dubai'},
            {'city': 'Dubai', 'cat': 'adventure', 'title': 'Red Dunes Desert 4x4 Safari & Bedouin BBQ', 'cost': 65.00, 'dur': 6.0, 'rating': 4.8, 'img': 'https://images.unsplash.com/photo-1451337516015-6b6e9a44a8a3?w=800&auto=format&fit=crop&q=80', 'loc': 'Lahbab Desert'},

            # Cairo
            {'city': 'Cairo', 'cat': 'culture', 'title': 'Giza Pyramids & Great Sphinx Private Guide', 'cost': 45.00, 'dur': 4.0, 'rating': 4.9, 'img': 'https://images.unsplash.com/photo-1572252009286-268acec5ca0a?w=800&auto=format&fit=crop&q=80', 'loc': 'Al Haram, Giza'},
            {'city': 'Cairo', 'cat': 'sightseeing', 'title': 'Grand Egyptian Museum Treasures Tour', 'cost': 40.00, 'dur': 3.5, 'rating': 4.8, 'img': 'https://images.unsplash.com/photo-1503177119275-0aa32b3a9368?w=800&auto=format&fit=crop&q=80', 'loc': 'Giza Plateau'},
        ]

        activity_map = {}
        for a in activities_data:
            if a['city'] in city_map and a['cat'] in cat_map:
                act_obj, _ = Activity.objects.get_or_create(
                    title=a['title'],
                    city=city_map[a['city']],
                    defaults={
                        'category': cat_map[a['cat']],
                        'estimated_cost': Decimal(str(a['cost'])),
                        'duration_hours': a['dur'],
                        'rating': a['rating'],
                        'image_url': a['img'],
                        'location_name': a['loc'],
                        'is_popular': True,
                        'description': f"Experience the finest {a['title']} with certified local experts, priority entrance, and captivating stories."
                    }
                )
                activity_map[a['title']] = act_obj

        # 6. Seed Complete Trips with Stops, Itinerary Items, and Expenses
        today = timezone.localdate()

        # TRIP 1: ONGOING (Alex Rivera) - "Grand Autumn Tour across Western Europe" (Paris -> Rome -> Barcelona)
        t1_start = today - timedelta(days=3)
        t1_end = today + timedelta(days=8)
        trip1, _ = Trip.objects.get_or_create(
            title="Grand Autumn Tour across Western Europe",
            user=alex,
            defaults={
                'description': "An exquisite 12-day multi-city journey uncovering culinary gems, legendary architecture, and romantic streets from Paris to Rome and coastal Barcelona.",
                'start_date': t1_start,
                'end_date': t1_end,
                'cover_image': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&auto=format&fit=crop&q=80',
                'status': 'ongoing',
                'total_budget': Decimal('3400.00'),
                'is_public': True,
                'likes_count': 42,
                'copies_count': 18,
                'views_count': 320
            }
        )

        # Stop 1: Paris
        s1, _ = TripStop.objects.get_or_create(
            trip=trip1,
            city=city_map['Paris'],
            defaults={
                'order': 1,
                'arrival_date': t1_start,
                'departure_date': t1_start + timedelta(days=3),
                'allocated_budget': Decimal('1200.00'),
                'notes': 'Arriving at CDG terminal 2E. Staying in Montmartre boutique loft.'
            }
        )
        # Itinerary items for Paris
        ItineraryItem.objects.get_or_create(
            trip_stop=s1,
            title="Eiffel Tower Summit & Champagne",
            defaults={
                'activity': activity_map.get('Eiffel Tower Summit & Champagne'),
                'cost': Decimal('45.00'),
                'day_number': 1,
                'date': t1_start,
                'start_time': '02:00 PM',
                'end_time': '04:30 PM',
                'category': 'activity',
                'is_completed': True,
                'notes': 'Breathtaking 360 panorama over Paris skyline'
            }
        )
        ItineraryItem.objects.get_or_create(
            trip_stop=s1,
            title="Montmartre Gourmet Food & Wine Walk",
            defaults={
                'activity': activity_map.get('Montmartre Gourmet Food & Wine Walk'),
                'cost': Decimal('85.00'),
                'day_number': 2,
                'date': t1_start + timedelta(days=1),
                'start_time': '11:00 AM',
                'end_time': '02:30 PM',
                'category': 'meal',
                'is_completed': True,
                'notes': 'Tasted aged Comte cheeses, fresh croissants, and Bordeaux reds'
            }
        )
        ItineraryItem.objects.get_or_create(
            trip_stop=s1,
            title="Louvre Masterpieces Guided Tour",
            defaults={
                'activity': activity_map.get('Louvre Masterpieces Guided Tour'),
                'cost': Decimal('65.00'),
                'day_number': 3,
                'date': t1_start + timedelta(days=2),
                'start_time': '10:00 AM',
                'end_time': '01:00 PM',
                'category': 'activity',
                'is_completed': True,
                'notes': 'Mona Lisa, Winged Victory, and Venus de Milo'
            }
        )

        # Stop 2: Rome
        s2, _ = TripStop.objects.get_or_create(
            trip=trip1,
            city=city_map['Rome'],
            defaults={
                'order': 2,
                'arrival_date': t1_start + timedelta(days=4),
                'departure_date': t1_start + timedelta(days=7),
                'allocated_budget': Decimal('1100.00'),
                'notes': 'High-speed flight to Fiumicino. Staying near Piazza Navona.'
            }
        )
        ItineraryItem.objects.get_or_create(
            trip_stop=s2,
            title="Colosseum & Roman Forum VIP Access",
            defaults={
                'activity': activity_map.get('Colosseum & Roman Forum VIP Access'),
                'cost': Decimal('55.00'),
                'day_number': 5,
                'date': t1_start + timedelta(days=4),
                'start_time': '09:30 AM',
                'end_time': '12:30 PM',
                'category': 'activity',
                'is_completed': False,
                'notes': 'Gladiator arena floor access with historical audio'
            }
        )
        ItineraryItem.objects.get_or_create(
            trip_stop=s2,
            title="Trastevere Artisanal Pasta & Gelato Masterclass",
            defaults={
                'activity': activity_map.get('Trastevere Artisanal Pasta & Gelato Masterclass'),
                'cost': Decimal('75.00'),
                'day_number': 6,
                'date': t1_start + timedelta(days=5),
                'start_time': '05:00 PM',
                'end_time': '08:30 PM',
                'category': 'meal',
                'is_completed': False,
                'notes': 'Learn handmade carbonara and creamy pistachio gelato'
            }
        )

        # Stop 3: Barcelona
        s3, _ = TripStop.objects.get_or_create(
            trip=trip1,
            city=city_map['Barcelona'],
            defaults={
                'order': 3,
                'arrival_date': t1_start + timedelta(days=8),
                'departure_date': t1_end,
                'allocated_budget': Decimal('1100.00'),
                'notes': 'Scenic flight to BCN airport. Coastal hotel in Barceloneta.'
            }
        )
        ItineraryItem.objects.get_or_create(
            trip_stop=s3,
            title="Sagrada Família Towers & Crypt Fast-Track",
            defaults={
                'activity': activity_map.get('Sagrada Família Towers & Crypt Fast-Track'),
                'cost': Decimal('40.00'),
                'day_number': 9,
                'date': t1_start + timedelta(days=8),
                'start_time': '10:00 AM',
                'end_time': '12:30 PM',
                'category': 'activity',
                'is_completed': False,
                'notes': 'Nativity facade tower climb'
            }
        )

        # Direct Expenses for Trip 1
        TripExpense.objects.get_or_create(
            trip=trip1,
            description="TGV & European regional flights bundle",
            defaults={'category': 'transport', 'amount': Decimal('480.00'), 'date': t1_start}
        )
        TripExpense.objects.get_or_create(
            trip=trip1,
            description="Boutique Montmartre Parisian hotel (3 nights)",
            defaults={'category': 'stay', 'amount': Decimal('520.00'), 'date': t1_start}
        )
        TripExpense.objects.get_or_create(
            trip=trip1,
            description="Piazza Navona Heritage Suites (3 nights)",
            defaults={'category': 'stay', 'amount': Decimal('490.00'), 'date': t1_start + timedelta(days=4)}
        )

        # TRIP 2: UPCOMING (Alex Rivera) - "Japan Cultural Odyssey & Cherry Blossoms" (Tokyo -> Kyoto)
        t2_start = today + timedelta(days=20)
        t2_end = today + timedelta(days=29)
        trip2, _ = Trip.objects.get_or_create(
            title="Japan Cultural Odyssey & Cherry Blossoms",
            user=alex,
            defaults={
                'description': "Exploring Tokyo's electric neon metropolis followed by traditional Zen temples, bamboo forests, and tea ceremonies in ancient Kyoto.",
                'start_date': t2_start,
                'end_date': t2_end,
                'cover_image': 'https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=800&auto=format&fit=crop&q=80',
                'status': 'upcoming',
                'total_budget': Decimal('2800.00'),
                'is_public': True,
                'likes_count': 64,
                'copies_count': 29,
                'views_count': 450
            }
        )
        s_tokyo, _ = TripStop.objects.get_or_create(
            trip=trip2,
            city=city_map['Tokyo'],
            defaults={'order': 1, 'arrival_date': t2_start, 'departure_date': t2_start + timedelta(days=4), 'allocated_budget': Decimal('1500.00')}
        )
        ItineraryItem.objects.get_or_create(
            trip_stop=s_tokyo,
            title="Shibuya Sky & Scramble Crossing",
            defaults={'activity': activity_map.get('Shibuya Sky & Scramble Crossing'), 'cost': Decimal('22.00'), 'day_number': 1, 'category': 'activity', 'start_time': '04:00 PM', 'end_time': '06:00 PM'}
        )
        ItineraryItem.objects.get_or_create(
            trip_stop=s_tokyo,
            title="Tsukiji Outer Market Tasting Tour",
            defaults={'activity': activity_map.get('Tsukiji Outer Market Tasting Tour'), 'cost': Decimal('70.00'), 'day_number': 2, 'category': 'meal', 'start_time': '09:00 AM', 'end_time': '12:00 PM'}
        )
        s_kyoto, _ = TripStop.objects.get_or_create(
            trip=trip2,
            city=city_map['Kyoto'],
            defaults={'order': 2, 'arrival_date': t2_start + timedelta(days=5), 'departure_date': t2_end, 'allocated_budget': Decimal('1300.00')}
        )
        ItineraryItem.objects.get_or_create(
            trip_stop=s_kyoto,
            title="Fushimi Inari Thousand Torii Shrine Morning Walk",
            defaults={'activity': activity_map.get('Fushimi Inari Thousand Torii Shrine Morning Walk'), 'cost': Decimal('15.00'), 'day_number': 6, 'category': 'sightseeing', 'start_time': '07:30 AM', 'end_time': '10:30 AM'}
        )

        # TRIP 3: UPCOMING (Sophia Chen) - "Indonesian Tropical Paradise Escape" (Bali)
        t3_start = today + timedelta(days=35)
        t3_end = today + timedelta(days=42)
        trip3, _ = Trip.objects.get_or_create(
            title="Indonesian Tropical Paradise Escape",
            user=sophia,
            defaults={
                'description': "Immerse in holistic wellness retreats, sunrise volcano trekking, and sacred sea temples in mystical Bali.",
                'start_date': t3_start,
                'end_date': t3_end,
                'cover_image': 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800&auto=format&fit=crop&q=80',
                'status': 'upcoming',
                'total_budget': Decimal('1250.00'),
                'is_public': True,
                'likes_count': 51,
                'copies_count': 22,
                'views_count': 380
            }
        )
        s_bali, _ = TripStop.objects.get_or_create(
            trip=trip3,
            city=city_map['Bali'],
            defaults={'order': 1, 'arrival_date': t3_start, 'departure_date': t3_end, 'allocated_budget': Decimal('1250.00')}
        )
        ItineraryItem.objects.get_or_create(
            trip_stop=s_bali,
            title="Mount Batur Sunrise Volcano Trek & Hot Springs",
            defaults={'activity': activity_map.get('Mount Batur Sunrise Volcano Trek & Hot Springs'), 'cost': Decimal('45.00'), 'day_number': 2, 'category': 'adventure', 'start_time': '03:30 AM', 'end_time': '10:00 AM'}
        )
        ItineraryItem.objects.get_or_create(
            trip_stop=s_bali,
            title="Ubud Traditional Balinese Spa & Flower Bath",
            defaults={'activity': activity_map.get('Ubud Traditional Balinese Spa & Flower Bath'), 'cost': Decimal('35.00'), 'day_number': 3, 'category': 'relaxation', 'start_time': '02:00 PM', 'end_time': '04:30 PM'}
        )

        # TRIP 4: COMPLETED (Alex Rivera) - "Ultimate East Coast Metropolis Run" (New York City)
        t4_start = today - timedelta(days=60)
        t4_end = today - timedelta(days=55)
        trip4, _ = Trip.objects.get_or_create(
            title="Ultimate East Coast Metropolis Run",
            user=alex,
            defaults={
                'description': "5 days of Broadway magic, world-class dining, skyline views from glass observatories, and vibrant Greenwich Village jazz.",
                'start_date': t4_start,
                'end_date': t4_end,
                'cover_image': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800&auto=format&fit=crop&q=80',
                'status': 'completed',
                'total_budget': Decimal('1750.00'),
                'is_public': True,
                'likes_count': 38,
                'copies_count': 14,
                'views_count': 290
            }
        )
        s_nyc, _ = TripStop.objects.get_or_create(
            trip=trip4,
            city=city_map['New York City'],
            defaults={'order': 1, 'arrival_date': t4_start, 'departure_date': t4_end, 'allocated_budget': Decimal('1750.00')}
        )
        ItineraryItem.objects.get_or_create(
            trip_stop=s_nyc,
            title="Summit One Vanderbilt Glass Skydeck",
            defaults={'activity': activity_map.get('Summit One Vanderbilt Glass Skydeck'), 'cost': Decimal('48.00'), 'day_number': 1, 'category': 'sightseeing', 'is_completed': True, 'start_time': '11:00 AM', 'end_time': '01:00 PM'}
        )
        ItineraryItem.objects.get_or_create(
            trip_stop=s_nyc,
            title="Broadway Musical Premium Orchestra Seats",
            defaults={'activity': activity_map.get('Broadway Musical Premium Orchestra Seats'), 'cost': Decimal('140.00'), 'day_number': 2, 'category': 'nightlife', 'is_completed': True, 'start_time': '07:30 PM', 'end_time': '10:30 PM'}
        )

        # TRIP 5: COMPLETED (Marcus Vance) - "Mysteries of the Nile & Pyramids of Giza" (Cairo)
        t5_start = today - timedelta(days=90)
        t5_end = today - timedelta(days=83)
        trip5, _ = Trip.objects.get_or_create(
            title="Mysteries of the Nile & Pyramids of Giza",
            user=marcus,
            defaults={
                'description': "Unraveling ancient pharaonic monuments, sunset felucca cruises on the Nile, and camel treks across the Sahara sands.",
                'start_date': t5_start,
                'end_date': t5_end,
                'cover_image': 'https://images.unsplash.com/photo-1572252009286-268acec5ca0a?w=800&auto=format&fit=crop&q=80',
                'status': 'completed',
                'total_budget': Decimal('1100.00'),
                'is_public': True,
                'likes_count': 77,
                'copies_count': 35,
                'views_count': 510
            }
        )
        s_cairo, _ = TripStop.objects.get_or_create(
            trip=trip5,
            city=city_map['Cairo'],
            defaults={'order': 1, 'arrival_date': t5_start, 'departure_date': t5_end, 'allocated_budget': Decimal('1100.00')}
        )
        ItineraryItem.objects.get_or_create(
            trip_stop=s_cairo,
            title="Giza Pyramids & Great Sphinx Private Guide",
            defaults={'activity': activity_map.get('Giza Pyramids & Great Sphinx Private Guide'), 'cost': Decimal('45.00'), 'day_number': 2, 'category': 'culture', 'is_completed': True}
        )

        # 7. Wishlist / Saved Destinations for Alex
        SavedDestination.objects.get_or_create(user=alex, city=city_map['Tokyo'])
        SavedDestination.objects.get_or_create(user=alex, city=city_map['Rome'])
        SavedDestination.objects.get_or_create(user=alex, city=city_map['Santorini'])
        SavedDestination.objects.get_or_create(user=alex, city=city_map['Cape Town'])

        # 8. Community Comments & Likes
        TripLike.objects.get_or_create(user=alex, trip=trip3)
        TripLike.objects.get_or_create(user=alex, trip=trip5)
        TripLike.objects.get_or_create(user=sophia, trip=trip1)
        TripLike.objects.get_or_create(user=marcus, trip=trip1)

        TripComment.objects.get_or_create(
            user=sophia,
            trip=trip1,
            defaults={'comment': 'Such a wonderful route! The combination of Paris gastronomy with Rome historical walks is truly unmatched.'}
        )
        TripComment.objects.get_or_create(
            user=marcus,
            trip=trip1,
            defaults={'comment': 'Cloned this trip for my upcoming vacation in October! Thanks for sharing the detailed budget tips.'}
        )
        TripComment.objects.get_or_create(
            user=alex,
            trip=trip3,
            defaults={'comment': 'The Mount Batur sunrise hike in Bali looks breathtaking! Added to my personal bucket list.'}
        )

        self.stdout.write(self.style.SUCCESS("[+] Successfully seeded GlobeTrotter database with rich travel data!"))
