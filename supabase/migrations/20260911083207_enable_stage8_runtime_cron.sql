create extension if not exists pg_cron with schema pg_catalog;

comment on extension pg_cron is 'Scheduler usado apenas para invocar o worker de teste do IntegraSquad na Etapa 8.';
