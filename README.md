# Youtube Integration Simulation

This is a Django REST API small project that simulates YouTube like functionality with AI comment generation following guidelines

## Overview

Here is some technical things:
- YouTube style video and comment models
- RESTful API endpoints with Django REST Framework
- AI comment generation following Reengage System Message Offer Guidelines (main logic in apps/comments/ai_engine.py)
- Realistic mock data generation using Faker
- Simple Admin panel for content management (using Django admin site)
- Simple web UI for browsing videos and comments (Youtube alike)

## Tech stack

- Backend: Django 4.2, Django REST Framework
- Database: used SQLite for dev, then PostgreSQL later for docker
- AI Engine: Custom comment generation
- Mock data: Faker library for realistic content
- Docs: DRF Spectacular (Swagger/OpenAPI)
- Container: Docker and Docker Compose

## How to launch

- Using Docker and Docker Compose

1. **Start the app:**
```bash
docker-compose up --build
```
Create admin:
```bash
docker-compose exec web python manage.py createsuperuser
```

2. **Links:**
- Homepage: http://localhost:8000/
- Admin panel: http://localhost:8000/admin/
- API Docs: http://localhost:8000/api/docs/
- Videos UI: http://localhost:8000/videos/

Docker is already setup to automatically:
- Set up PostgreSQL database
- Run migrations
- Generate sample data (categories, videos, comments)
- Start the dev server

## On local

1. **Setup virtual env and run manage.py:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **DB setup:**
```bash
python manage.py migrate
```

3. **Generate sample data:**
```bash
python manage.py generate_categories
python manage.py generate_videos --count 50
python manage.py generate_comments --count 200
```

4. **Create superuser (optional):**
```bash
python manage.py createsuperuser
```

5. **Run the server:**
```bash
python manage.py runserver
```

## API Endpoints

### Core endpoints
- `GET /api/v1/videos/` - List videos with filtering and search
- `GET /api/v1/videos/{id}/` - Video details
- `GET /api/v1/videos/trending/` - Trending videos
- `GET /api/v1/comments/` - List comments
- `GET /api/v1/comments/{id}/` - Comment details

### AI comment generation
- `POST /api/v1/comments/generate_user_comments/` - Generate realistic user comments
- `POST /api/v1/comments/analyze_and_reply/` - Analyze comments and generate business replies
- `POST /api/v1/comments/generate_channel_promotion/` - Generate promotional comments

### API Calls for example

**Generate user comments:**
```bash
curl -X POST http://localhost:8000/api/v1/comments/generate_user_comments/ \
  -H "Content-Type: application/json" \
  -d '{"video_id": 1, "count": 5}'
```

**Generate business reples:**
```bash
curl -X POST http://localhost:8000/api/v1/comments/analyze_and_reply/ \
  -H "Content-Type: application/json" \
  -d '{"video_id": 1}'
```

## What is done according to context

- ${offer-info} Placeholder- proper system message approach
- Channel owner identity - business replies come from video channel owners
- Semantic opportunity detection - AI analyzes comments for engagement potential
- Plain text system messages - clean, LLM optimized format
- Consistent responses - no random variation, following guidelines

## Commands

Generate sample data:

```bash
python manage.py generate_categories
python manage.py generate_videos --count 100
python manage.py generate_comments --count 500 --ai-ratio 0.3
python manage.py test_celery_tasks --task all
python manage.py test_celery_tasks --task ai_comments
python manage.py test_celery_tasks --task video_stats
```

## Background tasks with celery

### scheduled
- AI comment generation (every 5 min): Generates realistic user comments and business replies for popular videos
- Video stats update (every 10 min): Updates view counts, likes, and engagement metrics
- Comment analysis and reply (every 10 min): Analyzes recent comments and generates business replies
- Engagement metrics (hourly): Calculates daily analytics and engagement scores
- Trending videos update (daily): Updates trending video rankings based on recent activity
- Data cleanup (daily): Removes old AI comments and analytics data

### Running Celery locally

```bash
redis-server

celery -A config worker --loglevel=info

celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# optional, monitor tasks
celery -A config flower
```

### Running with Docker

```bash
docker-compose up --build
```

## With more time, I would improve:

- Deploy to heroku
- Logs
- Finish testing units and integration tests
- Remake admin panel, get rid of django admin site and build my own (just for more flexibility and nicer looking design)
- Enhance UI with more interactive frontend features, more work with Bootstrap 5, more stats
- Advanced analytics, a more detailed engagement metrics
- AI commenting engine improvements, like enhance logic, polish analyzing and commenting, integrate actual LLM APIs (OpenAI, Claude), add sentiment analysis with ML models, implement more sophisticated business opportunity scoring, add A/B testing for different reply strategies
- Machine learning features - recommendation system for videos, predictive analytics for engagement, automated content categorization, how to run better marketing through video description and comments section (generate with ML help, similar thing with giving context to offers, etc..)