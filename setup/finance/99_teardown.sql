-- Removes the Keystone Financial demo (tables, views, semantic view, stages, search service) in one step.
USE ROLE WBR_OWNER;
DROP SCHEMA IF EXISTS WBR_DB.FINANCE_DEMO;
