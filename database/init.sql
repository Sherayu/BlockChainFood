CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TYPE food_category AS ENUM (
    'desserts', 'starters', 'main-course', 'baking', 'beverages', 'snacks'
);

CREATE TYPE region AS ENUM (
    'indian', 'south-asian', 'mexican', 'italian', 'mediterranean', 'east-asian', 'global'
);

CREATE TYPE alert_frequency AS ENUM (
    'hourly', 'daily', 'weekly'
);

CREATE TYPE difficulty_level AS ENUM (
    'easy', 'medium', 'hard'
);

CREATE TYPE ingredient_category AS ENUM (
    'dairy', 'meat', 'seafood', 'vegetable', 'fruit', 'grain', 'spice', 'condiment', 'other'
);

CREATE TYPE source_type AS ENUM (
    'blog', 'recipe_site', 'rss', 'social_reddit', 'social_pinterest', 'social_twitter', 'aggregator'
);

CREATE TYPE crawl_status AS ENUM (
    'running', 'stopped', 'error'
);

CREATE TABLE alert_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    frequency alert_frequency NOT NULL DEFAULT 'daily',
    categories JSONB NOT NULL DEFAULT '[]'::jsonb,
    regions JSONB NOT NULL DEFAULT '[]'::jsonb,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    last_sent TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE trending_food (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    category food_category NOT NULL,
    region region NOT NULL DEFAULT 'global',
    popularity_score FLOAT NOT NULL DEFAULT 0.0,
    trend_velocity FLOAT NOT NULL DEFAULT 0.0,
    source_urls JSONB NOT NULL DEFAULT '[]'::jsonb,
    description TEXT,
    image_url TEXT,
    discovered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_trending_food_name ON trending_food(name);
CREATE INDEX idx_trending_food_category ON trending_food(category);
CREATE INDEX idx_trending_food_region ON trending_food(region);
CREATE INDEX idx_trending_food_score ON trending_food(popularity_score DESC);
CREATE INDEX idx_trending_food_discovered ON trending_food(discovered_at DESC);

CREATE TABLE recipe (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    food_id UUID REFERENCES trending_food(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    url TEXT NOT NULL,
    source VARCHAR(255),
    source_type source_type NOT NULL DEFAULT 'recipe_site',
    rating FLOAT DEFAULT 0.0,
    difficulty difficulty_level DEFAULT 'medium',
    prep_time_minutes INTEGER,
    cook_time_minutes INTEGER,
    servings INTEGER,
    thumbnail_url TEXT,
    description TEXT,
    ingredients JSONB NOT NULL DEFAULT '[]'::jsonb,
    steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    tags JSONB DEFAULT '[]'::jsonb,
    nutrition JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recipe_food_id ON recipe(food_id);
CREATE INDEX idx_recipe_rating ON recipe(rating DESC);

CREATE TABLE stored_ingredient (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipe_id UUID NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    quantity VARCHAR(100),
    unit VARCHAR(100),
    category ingredient_category DEFAULT 'other',
    notes TEXT,
    stored_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stored_ingredient_recipe ON stored_ingredient(recipe_id);

CREATE TABLE crawl_source (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    source_type source_type NOT NULL,
    crawl_frequency_minutes INTEGER NOT NULL DEFAULT 60,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    last_crawl TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE crawl_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES crawl_source(id) ON DELETE CASCADE,
    url_crawled TEXT NOT NULL,
    status_code INTEGER,
    items_extracted INTEGER DEFAULT 0,
    error_message TEXT,
    crawled_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_crawl_log_source ON crawl_log(source_id);
CREATE INDEX idx_crawl_log_time ON crawl_log(crawled_at DESC);

CREATE TABLE bot_usage_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    command VARCHAR(100) NOT NULL,
    user_id BIGINT NOT NULL,
    username VARCHAR(255),
    parameters TEXT,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bot_usage_command ON bot_usage_log(command);
CREATE INDEX idx_bot_usage_time ON bot_usage_log(created_at DESC);
CREATE INDEX idx_bot_usage_user ON bot_usage_log(user_id);

CREATE TABLE trending_food_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    food_name VARCHAR(255) NOT NULL,
    category food_category NOT NULL,
    region region NOT NULL DEFAULT 'global',
    popularity_score FLOAT NOT NULL DEFAULT 0.0,
    trend_velocity FLOAT NOT NULL DEFAULT 0.0,
    source_count INTEGER DEFAULT 0,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_trending_history_date ON trending_food_history(snapshot_date DESC);
CREATE INDEX idx_trending_history_category ON trending_food_history(category);
CREATE UNIQUE INDEX idx_trending_history_unique ON trending_food_history(food_name, category, snapshot_date);

INSERT INTO alert_config (frequency, categories, regions, active) VALUES
    ('daily', '["desserts", "main-course", "baking"]', '["global"]', TRUE);

INSERT INTO crawl_source (name, url, source_type, crawl_frequency_minutes) VALUES
    ('AllRecipes', 'https://www.allrecipes.com', 'recipe_site', 120),
    ('Food Network', 'https://www.foodnetwork.com', 'recipe_site', 120),
    ('Serious Eats', 'https://www.seriouseats.com', 'blog', 180),
    ('BBC Good Food', 'https://www.bbcgoodfood.com', 'recipe_site', 120),
    ('Reddit r/cooking', 'https://www.reddit.com/r/cooking/hot.json', 'social_reddit', 60),
    ('Reddit r/food', 'https://www.reddit.com/r/food/hot.json', 'social_reddit', 60),
    ('Epicurious', 'https://www.epicurious.com', 'blog', 180),
    ('Bon Appetit', 'https://www.bonappetit.com', 'blog', 180);
