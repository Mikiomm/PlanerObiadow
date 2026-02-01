-- Migration: create dinners table
-- Run with: python scripts/apply_migrations.py

CREATE TABLE IF NOT EXISTS dinners (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    ingredients JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
