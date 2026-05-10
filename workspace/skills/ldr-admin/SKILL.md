---
name: ldr-admin
description: LDR Admin tools -- KPI, metrics, database queries, Railway logs, story monitor
metadata: {"openclaw": {"emoji": "📊"}}
---

# LDR Admin Tools

Вызывай через exec: `/app/ldr-tools/.venv/bin/python3 /app/ldr-tools/cli.py <tool> '<json_args>'`

Без аргументов: `/app/ldr-tools/.venv/bin/python3 /app/ldr-tools/cli.py <tool>`
С аргументами: `/app/ldr-tools/.venv/bin/python3 /app/ldr-tools/cli.py <tool> '{"key":"value"}'`

## Обзор и KPI (без аргументов)
- `ldr_overview` -- общий обзор: KPI, DAU, выручка, расходы. Для "как дела", "что происходит"
- `ldr_kpi_fast` -- быстрые KPI: messages, DAU, revenue, costs. Легкий запрос
- `ldr_live_pulse` -- пульс: кто онлайн, активные коннекты, cron здоровье
- `ldr_system_health` -- здоровье: Supabase, Redis, LLM провайдеры
- `ldr_business_alerts` -- критичные алерты, аномалии
- `ldr_command_center` -- полная картина: алерты + pending actions

## Метрики (без аргументов)
- `ldr_character_metrics` -- метрики персонажей: сообщения, trust, юзеры
- `ldr_community_kpi` -- KPI сообщества: DAU, подписки, engagement
- `ldr_user_segments` -- сегменты: по подпискам, trust, активности
- `ldr_unit_economics` -- ARPU, LTV, CAC, payback
- `ldr_moderation_stats` -- нарушения, блокировки
- `ldr_cron_health` -- статус cron задач
- `ldr_content_stats` -- контент: фото, видео, stories
- `ldr_timings` -- тайминги API: avg/min/max ms

## С аргументами period/days
- `ldr_revenue` -- выручка. Args: `{"period":"7d"}` или `{"days":30}`
- `ldr_costs` -- расходы AI. Args: `{"period":"7d"}` или `{"days":30}`
- `ldr_analytics` -- тренды. Args: `{"period":"7d"}` или `{"days":30}`
- `ldr_retention_cohorts` -- когорты. Args: `{"months":3}`
- `ldr_cost_analysis_sessions` -- дорогие сессии. Args: `{"period":"7d","limit":10}`
- `ldr_activity_feed` -- лента событий. Args: `{"limit":20}`

## Мониторинг
- `ldr_alerts` -- активные алерты Alert Engine: error rate, cron health, Redis, BER, LLM провайдеры. Без аргументов

## Railway Logs
- `railway_logs` -- логи Railway. Args: `{"service":"backend","lines":50,"filter":"error"}`
  - service: "backend" или "bot"
  - lines: до 100
  - filter: текст для фильтра

## Story Monitor
- `ldr_story_users` -- юзеры с stories. Args: `{"search":"email","subscription":"plus"}`
- `ldr_story_characters` -- персонажи юзера. Args: `{"user_id":"UUID"}`
- `ldr_story_details` -- детали stories. Args: `{"character_id":"sofia_003","user_id":"UUID"}`
- `ldr_story_single` -- одна story. Args: `{"story_id":"UUID"}`

## Supabase (прямые запросы к БД)

**Пример: последние 10 сообщений юзера с персонажем:**
```
supabase_query '{"table":"ldr_messages","select":"*","filters":"user_id=eq.8700b049-xxxx&character_id=eq.sofia_003","order":"created_at.desc","limit":10}'
```

- `supabase_query` -- SELECT. Args: `{"table":"users","select":"id,email","filters":"subscription_type=eq.plus","order":"created_at.desc","limit":10}`
- `supabase_count` -- COUNT. Args: `{"table":"users","filters":"subscription_type=eq.plus"}`
- `supabase_delete` -- DELETE (осторожно!). Args: `{"table":"violations","filters":"id=eq.UUID"}`
- `supabase_update` -- UPDATE (осторожно!). Args: `{"table":"users","filters":"id=eq.UUID","data":"{\"name\":\"New\"}"}`
- `supabase_insert` -- INSERT. Args: `{"table":"gift_catalog","data":"{\"name\":\"Gift\"}"}`

Формат фильтров PostgREST: `field=op.value` (eq, neq, gt, gte, lt, lte, like, ilike, in, is)
Несколько фильтров: `field1=eq.val1&field2=gt.val2`

## Таблицы (whitelist)
users, characters, user_matches, ldr_messages, memories, first_contacts, user_character_relationships, dialog_sessions, session_messages, schedules, schedule_overrides, scheduled_messages, gift_catalog, gift_purchases, gift_achievements, user_gift_achievements, gift_streaks, coin_transactions, stories, story_views, story_schedule, violations, blocks, gallery, photo_jobs, user_favorites, admins, admin_sessions, admin_logs, photo_reserves, photo_reserve_transactions, subscription_transactions

## ID форматы
- user_id = UUID (например: 550e8400-e29b-41d4-a716-446655440000)
- character_id = slug (например: sofia_003, mila_001, emma_002)
