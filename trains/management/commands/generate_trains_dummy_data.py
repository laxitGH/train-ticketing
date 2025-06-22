import random
from django.db import transaction
from datetime import time, timedelta
from django.core.management.base import BaseCommand
from trains.models import Station, Train, Route, RouteStation, RouteSchedule
from utils.enums import BookingType

"""
Enhanced generate_trains_dummy_data with more extensive data generation
"""

class TrainDataGenerator:
    
    # Extended Indian cities and their station codes (50 stations)
    STATIONS_DATA = [
        ("New Delhi", "Delhi", "Delhi", "NDLS"),
        ("Mumbai Central", "Mumbai", "Maharashtra", "MMCT"),
        ("Chennai Central", "Chennai", "Tamil Nadu", "MAS"),
        ("Kolkata", "Kolkata", "West Bengal", "KOAA"),
        ("Bangalore City", "Bangalore", "Karnataka", "SBC"),
        ("Hyderabad", "Hyderabad", "Telangana", "SC"),
        ("Ahmedabad", "Ahmedabad", "Gujarat", "ADI"),
        ("Pune", "Pune", "Maharashtra", "PUNE"),
        ("Jaipur", "Jaipur", "Rajasthan", "JP"),
        ("Lucknow", "Lucknow", "Uttar Pradesh", "LJN"),
        ("Kanpur", "Kanpur", "Uttar Pradesh", "CNB"),
        ("Nagpur", "Nagpur", "Maharashtra", "NGP"),
        ("Indore", "Indore", "Madhya Pradesh", "INDB"),
        ("Bhopal", "Bhopal", "Madhya Pradesh", "BPL"),
        ("Patna", "Patna", "Bihar", "PNBE"),
        ("Agra", "Agra", "Uttar Pradesh", "AGC"),
        ("Vadodara", "Vadodara", "Gujarat", "BRC"),
        ("Ludhiana", "Ludhiana", "Punjab", "LDH"),
        ("Coimbatore", "Coimbatore", "Tamil Nadu", "CBE"),
        ("Kochi", "Kochi", "Kerala", "ERS"),
        ("Visakhapatnam", "Visakhapatnam", "Andhra Pradesh", "VSKP"),
        ("Bhubaneswar", "Bhubaneswar", "Odisha", "BBS"),
        ("Guwahati", "Guwahati", "Assam", "GHY"),
        ("Dehradun", "Dehradun", "Uttarakhand", "DDN"),
        ("Jammu", "Jammu", "Jammu & Kashmir", "JAT"),
        # Additional 25 stations for more variety
        ("Surat", "Surat", "Gujarat", "ST"),
        ("Rajkot", "Rajkot", "Gujarat", "RJT"),
        ("Jodhpur", "Jodhpur", "Rajasthan", "JU"),
        ("Udaipur", "Udaipur", "Rajasthan", "UDZ"),
        ("Amritsar", "Amritsar", "Punjab", "ASR"),
        ("Chandigarh", "Chandigarh", "Chandigarh", "CDG"),
        ("Shimla", "Shimla", "Himachal Pradesh", "SML"),
        ("Haridwar", "Haridwar", "Uttarakhand", "HW"),
        ("Varanasi", "Varanasi", "Uttar Pradesh", "BSB"),
        ("Allahabad", "Allahabad", "Uttar Pradesh", "ALD"),
        ("Gwalior", "Gwalior", "Madhya Pradesh", "GWL"),
        ("Jabalpur", "Jabalpur", "Madhya Pradesh", "JBP"),
        ("Raipur", "Raipur", "Chhattisgarh", "R"),
        ("Bilaspur", "Bilaspur", "Chhattisgarh", "BSP"),
        ("Ranchi", "Ranchi", "Jharkhand", "RNC"),
        ("Jamshedpur", "Jamshedpur", "Jharkhand", "TATA"),
        ("Durgapur", "Durgapur", "West Bengal", "DGR"),
        ("Siliguri", "Siliguri", "West Bengal", "SGUJ"),
        ("Cuttack", "Cuttack", "Odisha", "CTC"),
        ("Berhampur", "Berhampur", "Odisha", "BAM"),
        ("Vijayawada", "Vijayawada", "Andhra Pradesh", "BZA"),
        ("Tirupati", "Tirupati", "Andhra Pradesh", "TPTY"),
        ("Guntur", "Guntur", "Andhra Pradesh", "GNT"),
        ("Warangal", "Warangal", "Telangana", "WL"),
        ("Mysore", "Mysore", "Karnataka", "MYS"),
        ("Hubli", "Hubli", "Karnataka", "UBL"),
        ("Mangalore", "Mangalore", "Karnataka", "MAQ"),
        ("Thiruvananthapuram", "Thiruvananthapuram", "Kerala", "TVC"),
        ("Kozhikode", "Kozhikode", "Kerala", "CLT"),
        ("Thrissur", "Thrissur", "Kerala", "TCR"),
        ("Salem", "Salem", "Tamil Nadu", "SA"),
    ]
    
    # Extended train names and numbers (60 trains) - All unique numbers
    TRAINS_DATA = [
        ("Rajdhani Express", "12951"),
        ("Shatabdi Express", "12002"),
        ("Duronto Express", "12259"),
        ("Garib Rath", "12910"),
        ("Jan Shatabdi", "12023"),
        ("Humsafar Express", "22887"),
        ("Tejas Express", "22119"),
        ("Vande Bharat", "22435"),
        ("Golden Temple Mail", "12903"),
        ("Mumbai Mail", "12617"),
        ("Chennai Express", "12841"),
        ("Kolkata Mail", "12313"),
        ("Karnataka Express", "12627"),
        ("Andhra Pradesh Express", "12723"),
        ("Gujarat Mail", "19031"),
        ("Punjab Mail", "12137"),
        ("Rajasthan Express", "12958"),
        ("Uttar Pradesh Sampark Kranti", "12565"),
        ("Maharashtra Express", "11401"),
        ("Tamil Nadu Express", "12621"),
        ("Kerala Express", "12626"),  # Changed from 12625 to avoid duplicate
        ("Odisha Sampark Kranti", "12896"),
        ("Assam Express", "15959"),
        ("Himalayan Queen", "14095"),
        ("Jammu Mail", "14033"),
        # Additional 35 trains with unique numbers
        ("Deccan Queen", "12123"),
        ("Flying Ranee", "12009"),
        ("Gitanjali Express", "12859"),
        ("Grand Trunk Express", "12615"),
        ("Howrah Express", "12869"),
        ("Island Express", "16331"),
        ("Janata Express", "12801"),
        ("Kanyakumari Express", "16339"),
        ("Lalbagh Express", "12607"),
        ("Mandovi Express", "10103"),
        ("Netravati Express", "16345"),
        ("Okha Express", "19567"),
        ("Poorva Express", "12303"),
        ("Quaternary Express", "12629"),  # Changed from 12625 to avoid duplicate
        ("Raptisagar Express", "12511"),
        ("Sampark Kranti Express", "12217"),
        ("Trivandrum Express", "16381"),
        ("Udyan Express", "19019"),
        ("Vikramshila Express", "12367"),
        ("West Coast Express", "16629"),
        ("Yesvantpur Express", "12613"),
        ("Zindagi Express", "14806"),  # Changed from 14805 to avoid duplicate
        ("Ajmer Express", "12957"),
        ("Bikaner Express", "14707"),
        ("Chetak Express", "12981"),
        ("Delhi Express", "12423"),
        ("Ekatmata Express", "19027"),
        ("Firozpur Express", "14015"),
        ("Gomti Express", "12419"),
        ("Hirakud Express", "18005"),
        ("Intercity Express", "12127"),
        ("Jhelum Express", "11077"),
        ("Kota Express", "12465"),
        ("Lucknow Express", "12229"),
        ("Malwa Express", "12919"),
        ("Navyug Express", "16317"),
        ("Orient Express", "16687"),
        ("Pawan Express", "14807"),  # Changed from 14805 to avoid duplicate
        ("Quetta Express", "14808"),  # Changed from 14805 to avoid duplicate
        ("Rewa Express", "11447"),
    ]
    
    # Route templates for more variety
    ROUTE_TEMPLATES = [
        "{source}-{dest} Express",
        "{source}-{dest} Mail",
        "{source}-{dest} Superfast",
        "{source} {dest} Link Express",
        "{source} {dest} Passenger",
        "{source}-{dest} Special",
        "{source} {dest} Intercity",
        "{source}-{dest} Rajdhani",
        "{source} {dest} Shatabdi",
        "{source}-{dest} Jan Shatabdi",
    ]
    
    WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    
    def __init__(self):
        self.stations = []
        self.trains = []
        self.routes = []
        # Track train schedules: {train_id: {weekday: [(start_time, end_time, duration_minutes)]}}
        self.train_schedules = {}
    
    @transaction.atomic
    def generate_all_data(self):
        """Generate all dummy data in the correct order"""
        print("🚀 Starting enhanced dummy data generation...")
        
        self.create_stations()
        self.create_trains()
        self.create_routes_with_schedules()
        
        print("✅ Enhanced dummy data generation completed!")
        print(f"📊 Created: {len(self.stations)} stations, {len(self.trains)} trains, {len(self.routes)} routes")
        
        # Print schedule statistics
        total_schedules = 0
        for train_id, weekday_schedules in self.train_schedules.items():
            for weekday, schedules in weekday_schedules.items():
                total_schedules += len(schedules)
        print(f"📅 Total schedules created: {total_schedules}")
    
    def create_stations(self):
        """Create 50 stations"""
        print("🏢 Creating stations...")
        
        for name, city, state, code in self.STATIONS_DATA:
            station = Station.objects.create(
                name=name,
                city=city,
                state=state,
                code=code
            )
            self.stations.append(station)
        
        print(f"✅ Created {len(self.stations)} stations")
    
    def create_trains(self):
        """Create 60 trains"""
        print("🚂 Creating trains...")
        
        for name, number in self.TRAINS_DATA:
            train = Train.objects.create(
                name=name,
                number=number,
            )
            self.trains.append(train)
            # Initialize schedule tracking for this train
            self.train_schedules[train.id] = {day: [] for day in self.WEEKDAYS}
        
        print(f"✅ Created {len(self.trains)} trains")
    
    def create_routes_with_schedules(self):
        """Create 150-200 routes with realistic schedules and no conflicts"""
        print("🛤️  Creating routes with schedules...")
        
        route_count = 0
        target_routes = 200  # Much higher target for more variations
        max_attempts = 800   # More attempts for better coverage
        failed_attempts = 0
        
        # Track popular station pairs for creating multiple routes
        self.popular_pairs = []
        self.route_pairs = {}  # Track existing routes between station pairs
        
        # Define popular station pairs (major cities) that should have multiple routes
        major_stations = [s for s in self.stations if s.code in [
            'NDLS', 'MMCT', 'MAS', 'KOAA', 'SBC', 'SC', 'ADI', 'PUNE', 'JP', 'LJN',
            'CNB', 'NGP', 'INDB', 'BPL', 'PNBE', 'AGC', 'BRC', 'LDH', 'CBE', 'ERS'
        ]]
        
        # Create popular pairs from major stations
        for i, station1 in enumerate(major_stations):
            for station2 in major_stations[i+1:]:
                self.popular_pairs.append((station1, station2))
        
        print(f"🎯 Identified {len(self.popular_pairs)} popular station pairs for multiple routes")
        
        while route_count < target_routes and max_attempts > 0:
            max_attempts -= 1
            
            # Decide whether to create a route between popular pairs (60% chance)
            # or random stations (40% chance)
            if random.random() < 0.6 and self.popular_pairs:
                # Choose from popular pairs, with higher probability for pairs with fewer existing routes
                pair_weights = []
                for source_station, dest_station in self.popular_pairs:
                    pair_key = tuple(sorted([source_station.id, dest_station.id]))
                    existing_routes = self.route_pairs.get(pair_key, 0)
                    # Higher weight for pairs with fewer routes (inverse weighting)
                    weight = max(1, 5 - existing_routes)  # Weight decreases as routes increase
                    pair_weights.append(weight)
                
                if pair_weights:
                    selected_pair = random.choices(self.popular_pairs, weights=pair_weights)[0]
                    source_station, dest_station = selected_pair
                    # Randomly decide direction
                    if random.random() < 0.5:
                        source_station, dest_station = dest_station, source_station
                else:
                    # Fallback to random selection
                    source_station = random.choice(self.stations)
                    dest_station = random.choice(self.stations)
            else:
                # Pick random source and destination
                source_station = random.choice(self.stations)
                dest_station = random.choice(self.stations)
            
            if source_station == dest_station:
                failed_attempts += 1
                continue
            
            # Track this route pair before route length calculation
            pair_key = tuple(sorted([source_station.id, dest_station.id]))
            existing_count = self.route_pairs.get(pair_key, 0) + 1
            
            # Determine route length (2-25 stations) with weighted distribution
            # 4-8 stations have the highest frequency as requested
            route_length_weights = {
                2: 8,    # 8% chance for 2 stations
                3: 10,   # 10% chance for 3 stations
                4: 20,   # 20% chance for 4 stations (high frequency)
                5: 22,   # 22% chance for 5 stations (highest frequency)
                6: 20,   # 20% chance for 6 stations (high frequency)
                7: 18,   # 18% chance for 7 stations (high frequency)
                8: 15,   # 15% chance for 8 stations (high frequency)
                9: 8,    # 8% chance for 9 stations
                10: 6,   # 6% chance for 10 stations
                11: 4,   # 4% chance for 11 stations
                12: 3,   # 3% chance for 12 stations
            }
            
            # For routes longer than 10 stations, use random choice
            # For multiple routes between same stations, vary the route length
            if existing_count > 1:
                # Create variety: some direct routes, some with more stops
                if existing_count == 2 and random.random() < 0.4:
                    # Second route more likely to be direct (2-3 stations)
                    num_stations = random.choice([2, 3])
                elif existing_count >= 3 and random.random() < 0.3:
                    # Third+ route might be longer with more stops
                    num_stations = random.randint(6, 12)
                else:
                    # Normal distribution
                    num_stations = random.choices(
                        list(route_length_weights.keys()),
                        weights=list(route_length_weights.values())
                    )[0]
            elif random.random() < 0.04:  # 4% chance for very long routes
                num_stations = random.randint(11, 25)
            else:
                num_stations = random.choices(
                    list(route_length_weights.keys()),
                    weights=list(route_length_weights.values())
                )[0]
            
            # Create route stations
            if num_stations == 2:
                all_route_stations = [source_station, dest_station]
            else:
                # Create intermediate stations
                num_intermediate = num_stations - 2
                available_stations = [s for s in self.stations if s not in [source_station, dest_station]]
                
                if len(available_stations) < num_intermediate:
                    num_intermediate = min(len(available_stations), num_intermediate)
                
                if num_intermediate <= 0:
                    all_route_stations = [source_station, dest_station]
                else:
                    intermediate_stations = random.sample(available_stations, num_intermediate)
                    all_route_stations = [source_station] + intermediate_stations + [dest_station]
            
            # Calculate journey time based on realistic factors
            base_time_per_station = random.randint(45, 90)  # 45-90 minutes between stations
            base_journey_minutes = (len(all_route_stations) - 1) * base_time_per_station
            
            # Add some randomness (±20%) but ensure valid range
            variation = max(30, int(base_journey_minutes * 0.2))  # At least 30 minutes variation
            min_time = max(60, base_journey_minutes - variation)
            max_time = base_journey_minutes + variation
            
            # Final safety check
            if min_time >= max_time:
                min_time = 60
                max_time = max(120, base_journey_minutes)
            
            total_journey_minutes = random.randint(min_time, max_time)
            
            # Determine train type and availability based on route characteristics
            is_long_distance = len(all_route_stations) > 8 or total_journey_minutes > 720  # 12+ hours
            
            if is_long_distance:
                # Long distance trains: prefer trains with fewer existing routes
                train_usage_count = []
                for train in self.trains:
                    usage_count = sum(len(schedules) for schedules in self.train_schedules[train.id].values())
                    train_usage_count.append((train, usage_count))
                
                # Sort by usage count and pick from least used trains
                train_usage_count.sort(key=lambda x: x[1])
                available_trains = [t[0] for t in train_usage_count[:30]]  # Pick from 30 least used trains
                max_weekdays = random.randint(1, 3)  # Long distance: 1-3 days per week
            else:
                # Short distance: can use any train
                available_trains = self.trains
                max_weekdays = random.randint(3, 6)  # Short distance: 3-6 days per week
            
            if not available_trains:
                failed_attempts += 1
                continue
            
            train = random.choice(available_trains)
            
            # Generate departure time with more realistic distribution
            # Peak hours: 6-10 AM, 4-8 PM
            # Off-peak: other times
            peak_hours = list(range(6, 11)) + list(range(16, 21))
            off_peak_hours = [h for h in range(24) if h not in peak_hours]
            
            if random.random() < 0.6:  # 60% chance for peak hours
                departure_hour = random.choice(peak_hours)
            else:
                departure_hour = random.choice(off_peak_hours)
            
            departure_minute = random.choice([0, 15, 30, 45])
            departure_time = time(departure_hour, departure_minute)
            
            # Calculate arrival time
            arrival_total_minutes = (departure_hour * 60 + departure_minute + total_journey_minutes)
            
            # Handle multi-day journeys
            days_to_add = arrival_total_minutes // (24 * 60)
            arrival_minutes_in_day = arrival_total_minutes % (24 * 60)
            arrival_hour = arrival_minutes_in_day // 60
            arrival_minute = arrival_minutes_in_day % 60
            arrival_time = time(arrival_hour, arrival_minute)
            
            # Find available weekdays for this train (improved conflict detection)
            available_weekdays = []
            for weekday in self.WEEKDAYS:
                if self.is_train_available(train.id, weekday, departure_time, arrival_time, total_journey_minutes):
                    available_weekdays.append(weekday)
            
            if len(available_weekdays) == 0:
                failed_attempts += 1
                continue  # Train not available on any day
            
            # Select weekdays
            num_days = min(max_weekdays, len(available_weekdays))
            selected_weekdays = random.sample(available_weekdays, random.randint(1, num_days))
            
            # Update the route pair count and create route name with variation
            self.route_pairs[pair_key] = existing_count
            if existing_count > 1:
                # Add variation to route names for multiple routes between same stations
                route_variations = [
                    "{source}-{dest} Express",
                    "{source}-{dest} Mail", 
                    "{source}-{dest} Superfast",
                    "{source} {dest} Link Express",
                    "{source}-{dest} Special",
                    "{source} {dest} Intercity",
                    "{source}-{dest} Rajdhani",
                    "{source} {dest} Shatabdi",
                    "{source}-{dest} Jan Shatabdi",
                    "{source}-{dest} Premium"
                ]
                # Use different template based on existing count
                template_index = (existing_count - 1) % len(route_variations)
                route_name = route_variations[template_index].format(
                    source=source_station.city,
                    dest=dest_station.city
                )
            else:
                route_name = random.choice(self.ROUTE_TEMPLATES).format(
                    source=source_station.city,
                    dest=dest_station.city
                )
            
            # Enhanced seat allocation (2-10 total seats, tatkal much less than general)
            total_seats = random.randint(2, 10)
            
            # Tatkal seats: 10-25% of total seats, minimum 1 seat
            tatkal_percentage = random.uniform(0.10, 0.25)
            tatkal_seats = max(1, int(total_seats * tatkal_percentage))
            general_seats = total_seats - tatkal_seats
            
            # Ensure general seats is always more than tatkal (except when total is 2)
            if total_seats > 2 and general_seats <= tatkal_seats:
                tatkal_seats = max(1, total_seats // 4)  # 25% or less
                general_seats = total_seats - tatkal_seats
            
            seats = {
                BookingType.GENERAL.value: general_seats,
                BookingType.TATKAL.value: tatkal_seats
            }
            
            # Realistic pricing based on distance and train type
            base_price = random.randint(100, 500) + (len(all_route_stations) * random.randint(50, 150))
            if is_long_distance:
                base_price += random.randint(200, 800)
            
            pricing = {
                BookingType.GENERAL.value: base_price,
                BookingType.TATKAL.value: int(base_price * random.uniform(1.2, 1.5))  # 20-50% premium
            }
            
            route = Route.objects.create(
                name=route_name,
                train=train,
                seats=seats,
                pricing=pricing
            )
            
            # Create route stations with consistent timing
            self.create_route_stations(route, all_route_stations, total_journey_minutes)
            
            # Create schedules for selected weekdays
            for weekday in selected_weekdays:
                RouteSchedule.objects.create(
                    route=route,
                    weekday=weekday,
                    departure_time=departure_time,
                    arrival_time=arrival_time
                )
                
                # Mark train as busy during this time
                self.train_schedules[train.id][weekday].append((
                    departure_time, 
                    arrival_time, 
                    total_journey_minutes
                ))
            
            self.routes.append(route)
            route_count += 1
            
            if route_count % 10 == 0:
                print(f"📈 Created {route_count} routes...")
        
        print(f"✅ Created {len(self.routes)} routes with schedules")
        if failed_attempts > 0:
            print(f"⚠️  Failed attempts due to conflicts: {failed_attempts}")
        
        # Print route pair statistics
        pairs_with_multiple_routes = sum(1 for count in self.route_pairs.values() if count > 1)
        total_multiple_routes = sum(count for count in self.route_pairs.values() if count > 1)
        max_routes_per_pair = max(self.route_pairs.values()) if self.route_pairs else 0
        
        print(f"🔄 Station pairs with multiple routes: {pairs_with_multiple_routes}")
        print(f"🚂 Total routes in multiple-route pairs: {total_multiple_routes}")
        print(f"📈 Maximum routes between any pair: {max_routes_per_pair}")
        
        # Show some examples of multiple routes
        multiple_route_examples = [(pair, count) for pair, count in self.route_pairs.items() if count > 1]
        if multiple_route_examples:
            print("🎯 Examples of station pairs with multiple routes:")
            # Sort by count descending and show top 5
            multiple_route_examples.sort(key=lambda x: x[1], reverse=True)
            for (station1_id, station2_id), count in multiple_route_examples[:5]:
                station1 = next(s for s in self.stations if s.id == station1_id)
                station2 = next(s for s in self.stations if s.id == station2_id)
                print(f"   {station1.city} ↔ {station2.city}: {count} routes")
    
    def create_route_stations(self, route, stations, total_journey_minutes):
        """Create route stations with realistic timing and distances"""
        current_time = 0
        current_distance = 0
        
        # Distribute time realistically across stations
        if len(stations) == 2:
            # Direct route
            time_segments = [total_journey_minutes]
        else:
            # Multiple stations - distribute time with realistic variation
            num_segments = len(stations) - 1
            base_time_per_segment = total_journey_minutes // num_segments
            time_segments = []
            remaining_time = total_journey_minutes
            
            for i in range(num_segments):
                if i == num_segments - 1:  # Last segment gets remaining time
                    segment_time = remaining_time
                else:
                    # Add realistic variation (±30% of base time)
                    variation = int(base_time_per_segment * 0.3)
                    min_time = max(20, base_time_per_segment - variation)  # Minimum 20 minutes
                    max_time = base_time_per_segment + variation
                    segment_time = random.randint(min_time, max_time)
                    remaining_time -= segment_time
                
                time_segments.append(segment_time)
        
        # Create route stations with realistic timing
        for order, station in enumerate(stations, 1):
            if order == 1:  # Source station
                arrival_time = 0
                departure_time = random.randint(0, 5)  # 0-5 minutes preparation time
                current_time = departure_time
            else:
                # Add travel time to reach this station
                travel_time = time_segments[order - 2]
                current_time += travel_time
                arrival_time = current_time
                
                if order == len(stations):  # Destination station
                    departure_time = arrival_time  # No departure from final station
                else:
                    # Realistic stop time based on station importance
                    # Major stations: 5-15 minutes, smaller stations: 2-8 minutes
                    major_stations = ["NDLS", "MMCT", "MAS", "KOAA", "SBC", "SC", "ADI", "PUNE", "JP"]
                    if station.code in major_stations:
                        stop_time = random.randint(5, 15)
                    else:
                        stop_time = random.randint(2, 8)
                    
                    departure_time = arrival_time + stop_time
                    current_time = departure_time
            
            # Calculate realistic distance (varies by terrain and route)
            if order > 1:
                # Distance roughly correlates with time, but with variation for terrain
                time_for_segment = time_segments[order - 2]
                # Average speed: 40-80 km/h depending on route type
                avg_speed = random.uniform(40, 80)
                segment_distance = (time_for_segment / 60) * avg_speed
                current_distance += segment_distance
            
            RouteStation.objects.create(
                order=order,
                route=route,
                station=station,
                arrival_minutes_from_source=arrival_time,
                departure_minutes_from_source=departure_time,
                distance_kms_from_source=round(current_distance, 2)
            )
    
    def is_train_available(self, train_id, weekday, departure_time, arrival_time, journey_duration_minutes):
        """Enhanced train availability check with better conflict detection"""
        existing_schedules = self.train_schedules[train_id][weekday]
        
        # Convert times to minutes for easier comparison
        dep_minutes = departure_time.hour * 60 + departure_time.minute
        arr_minutes = arrival_time.hour * 60 + arrival_time.minute
        
        # Handle overnight journeys
        if arr_minutes < dep_minutes:
            arr_minutes += 24 * 60
        
        for existing_dep, existing_arr, existing_duration in existing_schedules:
            existing_dep_minutes = existing_dep.hour * 60 + existing_dep.minute
            existing_arr_minutes = existing_arr.hour * 60 + existing_arr.minute
            
            # Handle overnight for existing schedule
            if existing_arr_minutes < existing_dep_minutes:
                existing_arr_minutes += 24 * 60
            
            # Enhanced buffer time calculation based on journey length
            # Longer journeys need more buffer time for maintenance, cleaning, etc.
            base_buffer = 90  # 1.5 hours minimum
            if journey_duration_minutes > 720:  # 12+ hours
                buffer_minutes = base_buffer + 60  # 2.5 hours for long distance
            elif journey_duration_minutes > 360:  # 6+ hours
                buffer_minutes = base_buffer + 30  # 2 hours for medium distance
            else:
                buffer_minutes = base_buffer  # 1.5 hours for short distance
            
            # Check for overlap with buffer time
            new_start = dep_minutes
            new_end = arr_minutes + buffer_minutes
            existing_start = existing_dep_minutes
            existing_end = existing_arr_minutes + buffer_minutes
            
            # Check if schedules overlap
            if not (new_end <= existing_start or new_start >= existing_end):
                return False
        
        return True
    
    def clear_all_data(self):
        """Clear all existing data"""
        print("🗑️  Clearing existing data...")
        RouteSchedule.objects.all().delete()
        RouteStation.objects.all().delete()
        Route.objects.all().delete()
        Train.objects.all().delete()
        Station.objects.all().delete()
        print("✅ All data cleared!")


# Convenience function to run the generator
def generate_dummy_data():
    generator = TrainDataGenerator()
    generator.clear_all_data()
    generator.generate_all_data()


def clear_dummy_data():
    generator = TrainDataGenerator()
    generator.clear_all_data() 


class Command(BaseCommand):
    help = 'Generate enhanced dummy train data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting enhanced dummy data generation...')
        )
        
        generator = TrainDataGenerator()
        
        if options['clear']:
            generator.clear_all_data()
            
        generator.generate_all_data()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Successfully generated enhanced dummy data!')
        ) 