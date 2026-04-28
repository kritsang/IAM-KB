-- Run this once in Supabase SQL Editor (Database → SQL Editor → New query)
-- This creates the vector similarity search function used by query.py

create or replace function match_documents(
  query_embedding vector(1536),
  match_count     int   default 5,
  match_threshold float default 0.3
)
returns table (
  id         uuid,
  content    text,
  metadata   jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  where 1 - (documents.embedding <=> query_embedding) > match_threshold
  order by documents.embedding <=> query_embedding
  limit match_count;
end;
$$;
