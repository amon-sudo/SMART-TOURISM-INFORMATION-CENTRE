-- Create user if not exists
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_user
      WHERE  usename = 'group_user') THEN

      CREATE USER group_user WITH PASSWORD 'teamwork123';
   END IF;
END
$do$;

-- Create database if not exists
SELECT 'CREATE DATABASE smart_tourism_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'smart_tourism_db')\gexec

-- Reset password
ALTER USER group_user WITH PASSWORD 'teamwork123';

-- Ensure privileges
GRANT ALL PRIVILEGES ON DATABASE smart_tourism_db TO group_user;
