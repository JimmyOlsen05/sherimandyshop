CREATE DATABASE ppes_db;
CREATE USER ppes_user WITH PASSWORD '<your-password>';
ALTER ROLE ppes_user SET client_encoding TO 'utf8';
ALTER ROLE ppes_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ppes_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ppes_db TO ppes_user;