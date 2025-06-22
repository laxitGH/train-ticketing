import random
from datetime import time
from django.db import transaction
from django.core.management.base import BaseCommand
from trains.models import Station, Train, Route, RouteStation, RouteSchedule

"""
generate_trains_dummy_data
"""

class TrainDataGenerator:
    
    # Indian cities and their station codes
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
    ]
    
    # Train names and numbers
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
        ("Kerala Express", "12625"),
        ("Odisha Sampark Kranti", "12896"),
        ("Assam Express", "15959"),
        ("Himalayan Queen", "14095"),
        ("Jammu Mail", "14033"),
    ]
    
    # Route names combining cities
    ROUTE_TEMPLATES = [
        "{source}-{dest} Express",
        "{source}-{dest} Mail",
        "{source}-{dest} Superfast",
        "{source} {dest} Link Express",
        "{source} {dest} Passenger",
    ]
    
    WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    
    def __init__(self):
        self.stations = []
        self.trains = []
        self.routes = []
        # Track train schedules: {train_id: {weekday: [(start_time, end_time)]}}
        self.train_schedules = {}
    
    @transaction.atomic
    def generate_all_data(self):
        """Generate all dummy data in the correct order"""
        print("Starting dummy data generation...")
        
        self.create_stations()
        self.create_trains()
        self.create_routes_with_schedules()
        
        print("Dummy data generation completed!")
        print(f"Created: {len(self.stations)} stations, {len(self.trains)} trains, {len(self.routes)} routes")
    
    def create_stations(self):
        """Create 25 stations"""
        print("Creating stations...")
        
        for name, city, state, code in self.STATIONS_DATA:
            station = Station.objects.create(
                name=name,
                city=city,
                state=state,
                code=code
            )
            self.stations.append(station)
        
        print(f"Created {len(self.stations)} stations")
    
    def create_trains(self):
        """Create 25 trains"""
        print("Creating trains...")
        
        for name, number in self.TRAINS_DATA:
            train = Train.objects.create(
                name=name,
                number=number,
            )
            self.trains.append(train)
            # Initialize schedule tracking for this train
            self.train_schedules[train.id] = {day: [] for day in self.WEEKDAYS}
        
        print(f"Created {len(self.trains)} trains")
    
    def create_routes_with_schedules(self):
        """Create 35 routes with realistic schedules"""
        print("Creating routes with schedules...")
        
        route_count = 0
        max_attempts = 200  # Increased attempts for more routes
        
        while route_count < 35 and max_attempts > 0:
            max_attempts -= 1
            
            # Pick random source and destination
            source_station = random.choice(self.stations)
            dest_station = random.choice(self.stations)
            
            if source_station == dest_station:
                continue
            
            # Determine route length (2-25 stations)
            num_stations = random.randint(2, 25)
            
            # For routes with only 2 stations, use source and dest directly
            if num_stations == 2:
                all_route_stations = [source_station, dest_station]
            else:
                # Create intermediate stations
                num_intermediate = num_stations - 2
                available_stations = [s for s in self.stations if s not in [source_station, dest_station]]
                
                if len(available_stations) < num_intermediate:
                    # Not enough stations available, reduce the route size
                    num_intermediate = len(available_stations)
                    if num_intermediate == 0:
                        all_route_stations = [source_station, dest_station]
                    else:
                        intermediate_stations = available_stations
                        all_route_stations = [source_station] + intermediate_stations + [dest_station]
                else:
                    intermediate_stations = random.sample(available_stations, num_intermediate)
                    all_route_stations = [source_station] + intermediate_stations + [dest_station]
            
            # Calculate total journey time based on number of stations
            # Short routes (2-5 stations): 1-6 hours
            # Medium routes (6-15 stations): 6-18 hours  
            # Long routes (16-25 stations): 18-36 hours
            if len(all_route_stations) <= 5:
                total_journey_minutes = random.randint(60, 360)  # 1-6 hours
                is_long_distance = False
            elif len(all_route_stations) <= 15:
                total_journey_minutes = random.randint(360, 1080)  # 6-18 hours
                is_long_distance = random.choice([True, False])
            else:
                total_journey_minutes = random.randint(1080, 2160)  # 18-36 hours
                is_long_distance = True
            
            # Pick a train based on route type
            if is_long_distance:
                # Long distance trains typically run on single route
                available_trains = []
                for t in self.trains:
                    # Check if train has any existing schedules
                    has_schedules = False
                    for weekday_schedules in self.train_schedules[t.id].values():
                        if len(weekday_schedules) > 0:
                            has_schedules = True
                            break
                    if not has_schedules:
                        available_trains.append(t)
                
                if not available_trains:
                    continue  # No available trains for long distance
                train = random.choice(available_trains)
                max_weekdays = random.randint(1, 3)  # Long distance: 1-3 days per week
            else:
                # Short distance trains can run multiple routes
                train = random.choice(self.trains)
                max_weekdays = random.randint(2, 6)  # Short distance: 2-6 days per week
            
            # Generate departure time and calculate if train is available
            departure_hour = random.randint(4, 23)
            departure_minute = random.choice([0, 15, 30, 45])
            departure_time = time(departure_hour, departure_minute)
            
            # Calculate arrival time
            arrival_total_minutes = (departure_hour * 60 + departure_minute + total_journey_minutes) % (24 * 60)
            arrival_hour = arrival_total_minutes // 60
            arrival_minute = arrival_total_minutes % 60
            arrival_time = time(arrival_hour, arrival_minute)
            
            # Find available weekdays for this train
            available_weekdays = []
            for weekday in self.WEEKDAYS:
                if self.is_train_available(train.id, weekday, departure_time, arrival_time, total_journey_minutes):
                    available_weekdays.append(weekday)
            
            if len(available_weekdays) == 0:
                continue  # Train not available on any day
            
            # Select random weekdays from available ones
            num_days = min(max_weekdays, len(available_weekdays))
            selected_weekdays = random.sample(available_weekdays, random.randint(1, num_days))
            
            # Create the route
            route_name = random.choice(self.ROUTE_TEMPLATES).format(
                source=source_station.city,
                dest=dest_station.city
            )
            
            route = Route.objects.create(
                name=route_name,
                train=train,
                total_seats=random.randint(3, 7),
                pricing={
                    "general": random.randint(500, 2000),
                    "tatkal": random.randint(700, 2800)
                }
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
            
            if route_count % 5 == 0:
                print(f"Created {route_count} routes...")
        
        print(f"Created {len(self.routes)} routes with schedules")
    
    def create_route_stations(self, route, stations, total_journey_minutes):
        """Create route stations with consistent timing"""
        current_time = 0
        current_distance = 0
        
        # Distribute time evenly across stations with some randomness
        if len(stations) == 2:
            # Direct route
            time_segments = [total_journey_minutes]
        else:
            # Multiple stations - distribute time
            base_time_per_segment = total_journey_minutes // (len(stations) - 1)
            time_segments = []
            remaining_time = total_journey_minutes
            
            for i in range(len(stations) - 1):
                if i == len(stations) - 2:  # Last segment
                    segment_time = remaining_time
                else:
                    # Add some randomness (±20% of base time)
                    variation = int(base_time_per_segment * 0.2)
                    segment_time = random.randint(
                        max(30, base_time_per_segment - variation),
                        base_time_per_segment + variation
                    )
                    remaining_time -= segment_time
                
                time_segments.append(segment_time)
        
        # Create route stations
        for order, station in enumerate(stations, 1):
            if order == 1:  # Source station
                arrival_time = 0
                departure_time = random.randint(0, 5)  # 0-5 minutes at source
                current_time = departure_time
            else:
                # Add travel time to reach this station
                travel_time = time_segments[order - 2]
                current_time += travel_time
                arrival_time = current_time
                
                if order == len(stations):  # Destination station
                    departure_time = arrival_time  # No departure from final station
                else:
                    # Stop time at intermediate station (2-10 minutes)
                    stop_time = random.randint(2, 10)
                    departure_time = arrival_time + stop_time
                    current_time = departure_time
            
            # Calculate distance (roughly proportional to time)
            if order > 1:
                segment_distance = time_segments[order - 2] * random.uniform(0.8, 1.2)  # km per minute varies
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
        """Check if train is available on given weekday and time"""
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
            
            # Check for overlap with buffer time (2 hours minimum gap)
            buffer_minutes = 120
            
            # Check if new schedule conflicts with existing
            if not (arr_minutes + buffer_minutes <= existing_dep_minutes or 
                    dep_minutes >= existing_arr_minutes + buffer_minutes):
                return False
        
        return True
    
    def clear_all_data(self):
        """Clear all existing data"""
        print("Clearing existing data...")
        RouteSchedule.objects.all().delete()
        RouteStation.objects.all().delete()
        Route.objects.all().delete()
        Train.objects.all().delete()
        Station.objects.all().delete()
        print("All data cleared!")


# Convenience function to run the generator
def generate_dummy_data():
    generator = TrainDataGenerator()
    generator.clear_all_data()
    generator.generate_all_data()


def clear_dummy_data():
    generator = TrainDataGenerator()
    generator.clear_all_data() 


class Command(BaseCommand):
    help = 'Generate dummy data for the train booking system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data',
        )
        parser.add_argument(
            '--clear-only',
            action='store_true',
            help='Only clear existing data, do not generate new data',
        )

    def handle(self, *args, **options):
        if options['clear_only']:
            self.stdout.write(
                self.style.WARNING('Clearing all existing dummy data...')
            )
            clear_dummy_data()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared all dummy data!')
            )
            return

        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing data before generating new data...')
            )
            clear_dummy_data()

        self.stdout.write(
            self.style.SUCCESS('Starting dummy data generation...')
        )
        
        try:
            generate_dummy_data()
            self.stdout.write(
                self.style.SUCCESS('Successfully generated dummy data!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating dummy data: {str(e)}')
            )
            raise 