-- Schema migrations for SurrealDB
-- Add your table definitions, indexes, and schema here

DEFINE NAMESPACE IF NOT EXISTS local_agent_memory;
USE NAMESPACE local_agent_memory;
DEFINE DATABASE IF NOT EXISTS main_database;
USE DATABASE main_database;

DEFINE TABLE agno_memories;
DEFINE FIELD created_at ON agno_memories TYPE string;
DEFINE FIELD updated_at ON agno_memories TYPE string;



-- Example:
-- DEFINE TABLE user SCHEMAFULL;
-- DEFINE FIELD name ON user TYPE string;
-- DEFINE FIELD email ON user TYPE string;
-- DEFINE INDEX email_idx ON user FIELDS email UNIQUE;
