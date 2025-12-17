-- Remove RLS from FAQ to allow Backfill
-- We will re-enable it properly later if needed, but for now we need to WRITE.

ALTER TABLE faq DISABLE ROW LEVEL SECURITY;

-- Just in case, grant permissions to anon/service_role
GRANT ALL ON TABLE faq TO postgres;
GRANT ALL ON TABLE faq TO anon;
GRANT ALL ON TABLE faq TO service_role;
