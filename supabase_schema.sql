-- Run this in your Supabase SQL Editor to create the sequences table.
-- This is optional — the app works without Supabase, but enables history.

create table if not exists sequences (
  id uuid default gen_random_uuid() primary key,
  linkedin_url text not null,
  company_url text not null,
  prospect_name text not null default '',
  company_name text not null default '',
  emails jsonb not null default '[]'::jsonb,
  created_at timestamptz default now()
);

-- Enable Row Level Security (optional, for production use)
-- alter table sequences enable row level security;
