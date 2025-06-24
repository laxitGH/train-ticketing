# Train Booking System

## Quick Start

### **Option 1: Use Pre-populated SQLite Database** (Recommended)

- **SQLite**: Used for faster development and testing
- **Pre-populated Database**: Included in git commits with dummy data
- **Ready to Use**: No database setup required - just clone and run!

```bash
git clone <repository-url>
cd train2
pip install -r requirements.txt
python manage.py runserver
```

### **Option 2: Alternative Database Setup**

If you want to use a different database:

1. Configure your database in `settings.py`
2. Run migrations: `python manage.py migrate`
3. Generate dummy data: `python manage.py generate_trains_dummy_data`

### **Create Test Users** (Optional):

```bash
python manage.py create_test_users
```

### **Login via API (Save Session)**:

```bash
# Login and save cookies to cookies.txt
curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123"}' \
  -c cookies.txt

# Use saved cookies for authenticated requests
curl -X GET http://localhost:8000/auth/details/ \
  -b cookies.txt
```

### **Access the Application**:

- **Admin Panel**: http://localhost:8000/admin/ (admin/admin123)
- **API Endpoints**: http://localhost:8000/api/
- **Test User**: testuser/test123

## Project Overview & Assumptions

### Core Entities

#### **1. Base Real-World Entities**

- **Train**: Physical train with unique number and name
- **Station**: Railway stations with unique codes (e.g., NDLS for New Delhi)

#### **2. Route System**

- **Route**: A journey path that a train follows between stations
- A single **train can run multiple routes** at different schedules
- Example: Train 12951 can run:
  - Route 1: Delhi → Mumbai (daily)
  - Route 2: Delhi → Chennai (weekly)
- Each route has **non-conflicting schedules** for any particular weekday

#### **3. Stop Mapping**

- **Stop**: Links a station to a route with specific details:
  - Order of station in the route
  - Arrival/departure times from source
  - Distance from source station
- Each route has multiple stops in sequential order

#### **4. Schedule System**

- **Schedule**: Defines when a route operates
  - Weekday (MON, TUE, etc.)
  - Departure and arrival times
  - Each route can have different schedules for different weekdays

#### **5. User System**

- **User**: Built on Django's authentication system
- Users can make multiple bookings
- Email-based notifications for departure reminders

### Booking System Logic

#### **Booking Windows**

1. **General Booking Window**:

   - Opens: 120 days before departure
   - Closes: 4 hours before scheduled departure
2. **Tatkal Booking Window**:

   - Opens: 2 hours before departure
   - Duration: 10 minutes window only
   - Books any leftover vacant seats

#### **Ticket Types**

**General Tickets:**

- ✅ Can be cancelled
- ✅ Can go on waiting list
- ✅ Auto-upgrade when someone cancels
- 🕐 Long booking window (120 days to 4 hours)

**Tatkal Tickets:**

- ❌ Cannot be cancelled
- ❌ No waiting list - only confirmed seats
- ✅ Higher pricing for urgent booking
- 🕐 Short booking window (10 minutes, 2 hours before departure)

#### **Booking Entity**

- **Booking**: Made against a specific schedule
- Links: User → Schedule → Source Stop → Destination Stop
- Contains: journey date, amount, booking type, status

### Technical Implementation

#### **Task Scheduling & Notifications**

- **Celery**: Used for background task scheduling and processing
- **Email Reminders**: Sent 30 minutes before train departure
- **Smart Detection**: Finds bookings with trains departing in exactly 30 minutes
- **Periodic Tasks**: Automated checking every minute for upcoming departures

#### **Data Integrity & Code Modularity**

- **Database Transactions**: Used to maintain data integrity during complex operations
- **Serializers**: Django REST Framework serializers for API data validation
- **Dataclasses**: Used for structured data handling and type safety
- **Base Utils**: Modular utility classes for common operations across apps
  - Model utilities for common fields and behaviors
  - Selector utilities for optimized database queries
  - Pagination utilities for API responses

### Development Setup

### Development Notes

- **AI Assistance**: Used AI tools for generating realistic dummy data and documentation and management commands.

## Database Analysis Commands

### Find Multiple Routes on Same Source-Destination-Weekday

**Command:**

```bash
python manage.py shell -c "
from trains.models import Station, Route, Stop, Schedule
from collections import defaultdict

route_groups = defaultdict(list)

for schedule in Schedule.objects.select_related('route__train').prefetch_related('route__stops_of_route__station'):
    route = schedule.route
    stops = route.stops_of_route.all().order_by('order')
  
    if len(stops) >= 2:
        source_code = stops.first().station.code
        dest_code = stops.last().station.code
        key = (source_code, dest_code, schedule.weekday)
        route_groups[key].append(route.train.number)

print('Source → Dest | Weekday | Train Count | Train Numbers')
print('-' * 60)
for (source, dest, weekday), trains in route_groups.items():
    if len(trains) > 1:
        print(f'{source} → {dest} | {weekday} | {len(trains)} trains | {trains}')
"
```

**Sample Results:**

```
Source → Dest | Weekday | Train Count | Train Numbers
------------------------------------------------------------
ADI → BPL | SAT | 2 trains | ['12229', '16687']
LDH → CNB | TUE | 2 trains | ['16331', '12910']
MAS → JP | FRI | 3 trains | ['12419', '12617', '12367']
NGP → PUNE | WED | 2 trains | ['12303', '14806']
```

**Station Codes:**

- ADI = Ahmedabad
- BPL = Bhopal
- LDH = Ludhiana
- CNB = Kanpur
- MAS = Chennai Central
- JP = Jaipur
- NGP = Nagpur
- PUNE = Pune
