-- Run this once in your Supabase SQL editor to enable pgvector.
-- The `vecs` library automatically handles collection (table) creation per session,
-- but pgvector must be enabled first.

create extension if not exists vector;

-- Optional: create a dedicated schema (vecs uses "vecs" schema by default)
create schema if not exists vecs;
