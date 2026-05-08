# Food Discovery Platform

A container-based microservices platform that monitors food & lifestyle feeds across websites, social media, blogs, and viral recipe aggregators to identify trending foods and recipes. Delivers daily alerts via Telegram bot with configurable categories, regions, and frequencies.

## Architecture Overview

```mermaid
graph TB
    subgraph External["External Sources"]
        S1[Food Blogs]
        S2[Recipe Sites]
        S3[RSS Feeds]
        S4[Social Media APIs]
    end

    subgraph Platform["Food Discovery Platform"]
        subgraph Crawler["Crawler Service - Python/Scrapy"]
            CS[Scrapy Spiders]
            PS[Playwright Scraper]
            RS[RSS Parser]
            SC[Social Clients]
        end

        subgraph Queue["Message Broker - Redis"]
            Q1[(Task Queue)]
        end

        subgraph Analysis["Analysis Service - Python/Celery"]
            PD[Process Crawl Data]
            TD[Trend Detection]
            IE[Ingredient Extraction]
            PS2[Popularity Scoring]
        end

        subgraph API["API Gateway - FastAPI"]
            GW[REST Endpoints]
            SW[OpenAPI Docs]
        end

        subgraph DB["Data Layer - PostgreSQL"]
            TF[(trending_food)]
            RC[(recipe)]
            SI[(stored_ingredient)]
            AC[(alert_config)]
        end

        subgraph Bot["Telegram Bot - python-telegram-bot"]
            CH[Command Handlers]
            AS[Alert Scheduler]
            NK[Inline Keyboards]
        end
    end

    S1 --> Crawler
    S2 --> Crawler
    S3 --> Crawler
    S4 --> Crawler

    Crawler --> Q1
    Q1 --> Analysis
    Analysis --> DB
    DB --> API
    API --> Bot
    Bot --> DB

    Bot --> Users[Telegram Users]
```

## System Components

### 1. Crawler Service (`crawler-service/`)

Multi-source data collection from food & lifestyle platforms.

```mermaid
graph LR
    subgraph Sources["Data Sources"]
        A[AllRecipes]
        B[Food Network]
        C[Serious Eats]
        D[BBC Good Food]
        E[Reddit r/cooking]
        F[Reddit r/food]
        G[Twitter/X]
        H[Pinterest]
    end

    subgraph Crawlers["Crawler Strategies"]
        I[Recipe Site Spider]
        J[Food Blog Spider]
        K[RSS Spider]
        L[Social API Clients]
    end

    subgraph Output["Output Pipeline"]
        M[Data Normalizer]
        N[Redis Publisher]
    end

    A --> I
    B --> I
    C --> J
    D --> I
    E --> L
    F --> L
    G --> L
    H --> L

    I --> M
    J --> M
    K --> M
    L --> M
    M --> N
    N --> O[(Redis Queue)]
```

**Spiders**:
- `recipe_site_spider.py` - Structured recipe data from AllRecipes, Food Network, BBC Good Food, Tasty
- `blog_spider.py` - Food blog extraction (Serious Eats, Bon Appetit, Epicurious, Food52)
- `rss_spider.py` - RSS feed monitoring (feedparser-based)
- `dynamic_scraper.py` - Playwright for JavaScript-heavy sites
- `reddit_client.py` - Reddit API integration (r/cooking, r/food, r/recipes)
- `pinterest_client.py` - Pinterest API trending pins
- `twitter_client.py` - Twitter/X API trending hashtags

### 2. Analysis Service (`analysis-service/`)

Processes raw crawled data through Celery workers.

```mermaid
graph TD
    subgraph Input["Redis Queue"]
        A[(Crawl Results)]
    end

    subgraph Workers["Celery Workers"]
        B[Process Crawl Data]
        C[Detect Food Trends]
        D[Extract Ingredients]
    end

    subgraph Processing["Processing Pipeline"]
        E[Deduplicator]
        F[Recipe Extractor]
        G[Popularity Scorer]
        H[Ingredient Parser]
        I[NLP Text Analyzer]
    end

    A --> B
    B --> C
    B --> D

    B --> E
    B --> F
    C --> G
    D --> H
    F --> I
```

**Trend Scoring Algorithm**:
```
score = (frequency_weight × 0.4) + (velocity_weight × 0.3) + 
        (source_diversity × 0.2) + (engagement × 0.1)
```

### 3. API Gateway (`api-gateway/`)

FastAPI-based REST API with auto-generated OpenAPI documentation.

```mermaid
graph LR
    subgraph Endpoints["API Endpoints"]
        A["/api/v1/config/alerts"]
        B[/api/v1/foods/trending]
        C[/api/v1/foods/{id}/recipes]
        D[/api/v1/recipes/{id}]
        E[/api/v1/recipes/{id}/ingredients]
        F[/api/v1/categories]
        G[/api/v1/regions]
        H[/api/v1/crawler/status]
        I[/api/v1/analysis/status]
    end

    subgraph Services["Service Layer"]
        J[Config Service]
        K[Food Service]
        L[Recipe Service]
        M[Ingredient Service]
    end

    subgraph Data["Data Layer"]
        N[(PostgreSQL)]
    end

    A --> J
    B --> K
    C --> L
    D --> L
    E --> M
    F --> J
    G --> J
    H --> K
    I --> K

    J --> N
    K --> N
    L --> N
    M --> N
```

**Endpoints**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/config/alerts` | Get alert configuration |
| PUT | `/api/v1/config/alerts` | Update alert configuration |
| GET | `/api/v1/config/alerts/all` | List all configurations |
| GET | `/api/v1/foods/trending` | Get trending foods |
| GET | `/api/v1/foods/{id}/recipes` | Get top 5 recipes for food |
| GET | `/api/v1/recipes/{id}` | Get recipe details |
| POST | `/api/v1/recipes/{id}/ingredients` | Extract & store ingredients |
| GET | `/api/v1/recipes/{id}/ingredients` | Get stored ingredients |
| GET | `/api/v1/categories` | List food categories |
| GET | `/api/v1/regions` | List cuisine regions |
| GET | `/api/v1/crawler/status` | Get crawler status |
| GET | `/api/v1/analysis/status` | Get analysis status |

### 4. Telegram Bot (`telegram-bot/`)

User interaction interface with command-based navigation and inline keyboards.

```mermaid
sequenceDiagram
    participant User as 👤 Telegram User
    participant Bot as 🤖 Bot Service
    participant API as 🌐 API Gateway
    participant DB as 💾 PostgreSQL

    User->>Bot: /start
    Bot-->>User: Welcome + Commands
    
    User->>Bot: /trending
    Bot->>API: GET /foods/trending
    API->>DB: Query trending foods
    DB-->>API: Food list
    API-->>Bot: JSON response
    Bot-->>User: 🔥 Trending Foods with Inline Buttons
    
    User->>Bot: [Tap: Select Food]
    Bot->>API: GET /foods/{id}/recipes
    API->>DB: Query recipes
    DB-->>API: Top 5 recipes
    API-->>Bot: Recipe list
    Bot-->>User: 🍽️ Recipe Cards with Buttons
    
    User->>Bot: [Tap: Select Recipe]
    Bot->>API: GET /recipes/{id}
    API-->>Bot: Full recipe details
    Bot-->>User: 📖 Recipe + Extract Button
    
    User->>Bot: [Tap: Extract Ingredients]
    Bot->>API: POST /recipes/{id}/ingredients
    API->>DB: Store ingredients
    DB-->>API: Confirmation
    API-->>Bot: Ingredients stored
    Bot-->>User: ✅ Ingredients by Category
```

**Bot Commands**:

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot with welcome message |
| `/help` | Show all available commands |
| `/categories` | Select food categories via inline keyboard |
| `/regions` | Select cuisine regions via inline keyboard |
| `/trending` | Get current trending foods |
| `/trending <category>` | Filter trending by category |
| `/recipes <food_name>` | Get top 5 recipes for a food |
| `/ingredients <recipe_id>` | Extract and store ingredients |
| `/configure` | Configure alert preferences |
| `/status` | View system status |

## Design Patterns

```mermaid
mindmap
  root((Design Patterns))
    Microservices
      Independent Deployment
      Single Responsibility
      Event-Driven Communication
    Repository
      Abstracted Data Access
      Testable Queries
      Database Independence
    Strategy
      Crawler Spiders
      Source-Specific Extraction
      Scoring Algorithms
    Observer
      Alert Scheduler
      User Notifications
      Event Callbacks
    Factory
      Spider Creation
      Parser Selection
      Handler Registration
    Circuit Breaker
      External API Calls
      Rate Limiting
      Graceful Degradation
```

| Pattern | Location | Implementation |
|---------|----------|----------------|
| **Microservices** | Overall architecture | 6 independent services in Docker containers |
| **Event-Driven** | Crawler → Analysis | Redis queue, Celery workers |
| **Repository** | Data layer | `BaseRepository<T>` with SQLAlchemy |
| **Strategy** | Crawler module | Different spider class per source type |
| **Observer** | Telegram notifications | APScheduler, callback handlers |
| **Factory** | Component creation | Crawler process, bot handlers |
| **Circuit Breaker** | External APIs | Try/except with fallback values |

## Data Flow

### Data Ingestion Pipeline

```mermaid
sequenceDiagram
    participant Src as External Sources
    participant Cr as Crawler Service
    participant MQ as Redis Queue
    participant An as Analysis Service
    participant DB as PostgreSQL

    loop Every 60 minutes
        Src->>Cr: Raw HTML/JSON/API data
        Cr->>Cr: Scrape & parse
        Cr->>Cr: Normalize data
        Cr->>MQ: Publish structured item
        MQ->>An: Celery worker picks up
        An->>An: Deduplicate
        An->>An: Extract recipe structure
        An->>An: Score popularity
        An->>An: Categorize food
        An->>DB: Store recipe & ingredients
        An->>DB: Update/insert trending food
    end
```

### Daily Alert Flow

```mermaid
sequenceDiagram
    participant Sch as APScheduler
    participant Bot as Telegram Bot
    participant API as API Gateway
    participant DB as PostgreSQL
    participant User as Telegram User

    Note over Sch: 08:00 UTC daily
    Sch->>Bot: Trigger daily alert
    Bot->>API: GET /config/alerts
    API->>DB: Query active config
    DB-->>API: Config (categories, regions)
    API-->>Bot: Configuration
    
    Bot->>API: GET /foods/trending
    API->>DB: Query trending foods
    DB-->>API: Today's trends
    API-->>Bot: Trending list
    
    Bot->>Bot: Format digest message
    
    loop Each subscriber
        Bot->>User: Send daily digest
        User-->>Bot: Tap for recipes
    end
    
    Bot->>API: PUT /config/alerts (update last_sent)
    API->>DB: Update timestamp
```

## Database Schema

```mermaid
erDiagram
    alert_config {
        UUID id PK
        varchar frequency
        jsonb categories
        jsonb regions
        boolean active
        timestamp last_sent
        timestamp created_at
        timestamp updated_at
    }

    trending_food {
        UUID id PK
        varchar name
        varchar category
        varchar region
        float popularity_score
        float trend_velocity
        jsonb source_urls
        text description
        text image_url
        timestamp discovered_at
        timestamp created_at
        timestamp updated_at
    }

    recipe {
        UUID id PK
        UUID food_id FK
        varchar title
        text url
        varchar source
        varchar source_type
        float rating
        varchar difficulty
        int prep_time_minutes
        int cook_time_minutes
        int servings
        text thumbnail_url
        text description
        jsonb ingredients
        jsonb steps
        jsonb tags
        jsonb nutrition
        timestamp created_at
    }

    stored_ingredient {
        UUID id PK
        UUID recipe_id FK
        varchar name
        varchar quantity
        varchar unit
        varchar category
        text notes
        timestamp stored_at
    }

    crawl_source {
        UUID id PK
        varchar name
        text url
        varchar source_type
        int crawl_frequency_minutes
        boolean active
        timestamp last_crawl
        timestamp created_at
        timestamp updated_at
    }

    crawl_log {
        UUID id PK
        UUID source_id FK
        text url_crawled
        int status_code
        int items_extracted
        text error_message
        timestamp crawled_at
    }

    trending_food ||--o{ recipe : has
    recipe ||--o{ stored_ingredient : contains
    crawl_source ||--o{ crawl_log : generates
```

## Directory Structure

```
food-discovery-platform/
├── docker-compose.yml          # All services, networks, volumes
├── .env.example                # Environment variables template
├── api-gateway/                # FastAPI REST API
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI entry point
│       ├── config.py           # Pydantic settings
│       ├── database.py         # SQLAlchemy async setup
│       ├── models/             # ORM models
│       ├── repositories/       # Data access layer
│       ├── routers/            # API endpoints
│       ├── schemas/            # Pydantic schemas (OAS)
│       └── middleware/         # Rate limiter
├── crawler-service/            # Scrapy + Playwright
│   ├── Dockerfile
│   ├── requirements.txt
│   └── crawler/
│       ├── settings.py         # Scrapy configuration
│       ├── runner.py           # Entry point
│       ├── spiders/            # Scrapy spiders
│       ├── playwright/         # Dynamic scraper
│       ├── social/             # API clients
│       ├── pipelines/          # Data processing
│       └── middlewares/        # Rate limiting
├── analysis-service/           # Celery workers
│   ├── Dockerfile
│   ├── requirements.txt
│   └── analysis/
│       ├── celery_app.py       # Celery configuration
│       ├── tasks/              # Background tasks
│       ├── processors/         # Business logic
│       └── nlp/               # Text analysis
├── telegram-bot/               # User interface
│   ├── Dockerfile
│   ├── requirements.txt
│   └── bot/
│       ├── main.py             # Entry point
│       ├── handlers/           # Command & callback handlers
│       ├── keyboards/          # Inline keyboard builders
│       ├── scheduler/          # Daily alert cron
│       └── formatters/         # Message formatting
├── database/
│   └── init.sql                # Schema + seed data
├── postman/
│   └── food-discovery-api.postman_collection.json
└── docs/
    └── api-reference.md
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### Setup

1. **Clone and configure**:
```bash
git clone <repo-url> food-discovery-platform
cd food-discovery-platform
cp .env.example .env
```

2. **Set your Telegram Bot Token** in `.env`:
```env
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
```

3. **Launch all services**:
```bash
docker-compose up --build
```

4. **Verify**:
- API Gateway: http://localhost:8000/docs (Swagger UI)
- Health Check: http://localhost:8000/health
- Start Telegram bot: https://t.me/your_bot_username

### Running without Docker

Each service can run independently:

```bash
# API Gateway
cd api-gateway
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Analysis Service
cd analysis-service
pip install -r requirements.txt
celery -A analysis.celery_app worker --loglevel=info

# Crawler Service
cd crawler-service
pip install -r requirements.txt
python -m crawler.runner

# Telegram Bot
cd telegram-bot
pip install -r requirements.txt
python -m bot.main
```

## API Documentation

Auto-generated Swagger UI is available at `http://localhost:8000/docs` when the API Gateway is running.

The OpenAPI specification includes all endpoints with request/response schemas, example values, and error codes.

## Telegram Bot Usage

### Command Examples

```
/start         → Welcome message with setup options
/categories    → Inline keyboard: 🍰 Desserts, 🥗 Starters, 🍛 Main Course...
/regions       → Inline keyboard: 🇮🇳 Indian, 🌏 South Asian, 🌮 Mexican...
/trending      → "🔥 Today's Trending Foods: 1. Tiramisu (92/100)..."
/trending desserts → Filter by category
/recipes tiramisu  → "🍽️ Top 5 Tiramisu Recipes: 1. Classic Italian ⭐⭐⭐⭐..."
/ingredients <id>  → "✅ Ingredients Stored: Mascarpone 500g, Eggs 3..."
```

### Alert Configuration

Configure via `/configure` command:
- **Frequency**: hourly, daily, weekly
- **Categories**: desserts, starters, main-course, baking, beverages, snacks
- **Regions**: indian, south-asian, mexican, italian, east-asian, mediterranean, global

Daily alerts are sent at **08:00 UTC** with trending foods and recipe recommendations.

## Postman Testing

Import `postman/food-discovery-api.postman_collection.json` into Postman.

Set environment variables:
| Variable | Value |
|----------|-------|
| `base_url` | `http://localhost:8000` |
| `food_id` | (auto-populated from first request) |
| `recipe_id` | (auto-populated from first request) |

### Test Cases Included

- Health check
- CRUD operations for alert configuration
- Category and region listing
- Trending food queries with filters
- Recipe retrieval and details
- Ingredient extraction and storage
- Error handling (404, invalid params)
- System status endpoints

## Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| API Framework | FastAPI 0.104+ | REST API with auto OpenAPI |
| ORM | SQLAlchemy 2.0+ | Async database access |
| Database | PostgreSQL 15 | Primary data store |
| Message Queue | Redis 7 | Task queue + caching |
| Crawler | Scrapy 2.11+ | Structured web scraping |
| Dynamic Scraping | Playwright | JavaScript-heavy sites |
| Task Queue | Celery 5.3+ | Async processing |
| NLP | spaCy 3.7+ | Text analysis |
| Bot Framework | python-telegram-bot 20+ | Telegram integration |
| Container | Docker + Compose | Deployment |
| Data Formats | JSONB | Flexible ingredient storage |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `docker-compose up` and verify endpoints
4. Submit a pull request

## License

MIT License - See LICENSE file for details.
