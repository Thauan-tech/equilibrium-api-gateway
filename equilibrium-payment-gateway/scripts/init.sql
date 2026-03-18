-- Executado automaticamente pelo Postgres na primeira inicialização
-- Cria extensão para gerar UUIDs nativamente no banco

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- para busca por texto
