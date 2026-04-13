-- Skrypt inicjalizacyjny PostgreSQL.
-- Wykonywany automatycznie przy pierwszym starcie kontenera
-- (docker-entrypoint-initdb.d).
--
-- Tworzy dedykowaną bazę testową obok bazy produkcyjnej.
-- Baza produkcyjna (bonusapp) jest tworzona przez zmienną POSTGRES_DB.

CREATE DATABASE bonusapp_test;
GRANT ALL PRIVILEGES ON DATABASE bonusapp_test TO bonusapp;
