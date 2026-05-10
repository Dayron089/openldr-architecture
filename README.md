# OpenLDR — Telegram Ops Bot для FORELDR

Telegram бот-напарник, который следит за продакшеном FORELDR (AI-компаньоны) — KPI, расходы, ошибки, состояние LLM-провайдеров. Не дашборд, а оператор: думает над данными, замечает аномалии и сам пишет алерты.

Построен на [OpenClaw](https://github.com/openclaw/openclaw) (open-source AI gateway) с **Grok 4.1 Fast** в качестве мозга и **30 Python CLI tools** для доступа к Supabase, Railway и метрикам.

---

## Что умеет

**Утренний дайджест (каждый день в 22:00 UTC)** — DAU, подписки, выручка, расходы, маржа, новые платящие, балансы AI-аккаунтов. Если всё штатно — 5 строк, без воды.

**Smart Monitor (каждые 30 минут)** — проверяет здоровье провайдеров (xAI, DeepSeek, OpenRouter, Redis, Supabase), error rate, cron-задачи. Алертит только по красным линиям, дедуплицирует повторы.

**Голосовые команды** — отправляешь в чат voice-сообщение, Whisper транскрибирует, Grok отвечает.

**Свободные запросы** — "сколько юзеров на премиуме", "покажи дорогих юзеров за неделю", "что в логах backend за последний час", "сколько потратили на медиа", "какой плюс по юзеру email@x.com".

---

## Архитектура

```
Telegram ─► OpenClaw Gateway (Node, port 18789)
              │
              ├─► Grok 4.1 Fast (xAI) — мозг агента
              │
              └─► exec tool ─► Python CLI (30 tools)
                                  │
                                  ├─► Supabase (PostgreSQL)
                                  ├─► FORELDR backend API
                                  ├─► Railway API (логи)
                                  └─► Telegram (алерты)
```

**Деплой:** один Docker-контейнер на Railway, образ `ghcr.io/openclaw/openclaw:latest` + venv с Python tools поверх.

---

## Стек tools (30 штук)

| Категория | Tools |
|-----------|-------|
| **Обзор / KPI** | `ldr_overview`, `ldr_kpi_fast`, `ldr_live_pulse`, `ldr_command_center` |
| **Здоровье** | `ldr_system_health`, `ldr_business_alerts`, `ldr_alerts`, `ldr_cron_health` |
| **Метрики** | `ldr_character_metrics`, `ldr_community_kpi`, `ldr_user_segments`, `ldr_unit_economics` |
| **Финансы** | `ldr_revenue`, `ldr_costs`, `ldr_financial_balances`, `ldr_costs_users` |
| **Аналитика** | `ldr_analytics`, `ldr_retention_cohorts`, `ldr_subscription_analytics`, `ldr_trust_funnel` |
| **Контент** | `ldr_content_stats`, `ldr_timings`, `ldr_moderation_stats` |
| **Сессии** | `ldr_cost_analysis_sessions`, `ldr_activity_feed` |
| **Stories** | `ldr_story_users`, `ldr_story_characters`, `ldr_story_details`, `ldr_story_single` |
| **Railway** | `railway_logs` |
| **Supabase** | `supabase_query`, `supabase_count`, `supabase_update`, `supabase_delete`, `supabase_insert` |
| **Алерты** | `ldr_send_alert`, `ldr_resolve_alert` |

Все вызываются единообразно:

```bash
/app/ldr-tools/.venv/bin/python3 /app/ldr-tools/cli.py <tool_name> '{"key":"value"}'
```

---

## Структура

```
.
├── Dockerfile.ldr          # OpenClaw + Python venv в одном образе
├── railway.toml            # Railway config (builder=DOCKERFILE)
├── openclaw.json           # Модель, Telegram, exec sandbox, Whisper STT
├── cron/
│   └── jobs.json           # Утренний дайджест + Smart Monitor (каждые 30 мин)
├── ldr-tools/
│   ├── cli.py              # 30 Python tools (Supabase / Railway / KPI)
│   └── requirements.txt
└── workspace/
    ├── AGENTS.md           # Системный промпт агента (правила, quick reference)
    ├── PLAYBOOK.md         # Паттерны диагностики, follow-ups, красные линии
    ├── SOUL.md             # Характер агента — "не дашборд, а оператор"
    └── skills/
        └── ldr-admin/
            └── SKILL.md    # Документация tools для агента
```

`AGENTS.md` + `PLAYBOOK.md` + `SOUL.md` — это память агента между сессиями. Каждая новая сессия Grok начинает с чтения этих файлов: кто он, как думать, как анализировать.

---

## Конфиг (ключевое)

```jsonc
// openclaw.json
{
  "models": { "providers": { "xai": { "models": [{ "id": "grok-4-1-fast-non-reasoning" }] } } },
  "agents": {
    "defaults": {
      "model": { "primary": "xai/grok-4-1-fast-non-reasoning" },
      "models": { "xai/grok-4-1-fast-non-reasoning": { "params": { "temperature": 0.3 } } }
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "dmPolicy": "allowlist",
      "allowFrom": ["${ADMIN_USER_ID}"]
    }
  },
  "tools": {
    "exec": { "host": "gateway", "security": "full", "ask": "off" },
    "media": { "audio": { "enabled": true, "language": "ru", "echoTranscript": true } }
  }
}
```

- `temperature 0.3` — мало галлюцинаций при анализе чисел
- `dmPolicy: allowlist` — отвечает только админу, всех остальных игнорит
- `exec.security: full` + `ask: off` — Grok сам решает какой tool вызвать без запроса подтверждения
- Whisper STT для voice-команд (язык русский, эхо транскрипта в чат)

---

## Cron-задачи

```jsonc
// cron/jobs.json
[
  {
    "id": "ldr-morning-digest",
    "schedule": { "expr": "0 22 * * *", "tz": "UTC" },
    "payload": { "message": "Утренний дайджест: ldr_kpi_fast → ldr_business_alerts → ldr_financial_balances..." }
  },
  {
    "id": "ldr-smart-monitor",
    "schedule": { "expr": "*/30 * * * *" },
    "payload": { "message": "Проверь системы. Алерт только если красная линия (LLM down, error rate > 5%, ...)" }
  }
]
```

Cron не дёргает API напрямую — вместо этого отдаёт промпт агенту, который сам решает какие tools вызвать и в каком порядке. Если данные нормальные — пишет короткое "OK", если аномалия — формирует алерт по своим правилам из `PLAYBOOK.md`.

---

## Запуск

### Railway (production)

```bash
railway up
# или push в main → автодеплой
```

### Environment variables

См. `.env.example` — нужны токены Telegram, xAI, OpenAI (Whisper), Supabase service role, Railway API, креды backend.

### Локально

```bash
docker build -f Dockerfile.ldr -t openldr .
docker run --env-file .env -p 18789:18789 openldr
```

---

## Принципы агента (SOUL.md)

> Ты не dashboard-бот. Ты операционный напарник.

- **Цифра без контекста бесполезна** — DAU 15 это много или мало? Сравни со вчера, с неделей назад
- **Не жди вопроса "а почему"** — увидел аномалию, сразу копай глубже
- **Имей мнение** — "Этот юзер дорогой, но при Premium маржа ок" лучше голых чисел
- **Ошибки важнее метрик** — сломанный сервис > падение DAU
- **Если всё ок — скажи "всё ок"** — не лей воду

Telegram форматирование без Markdown (звёздочки и хэштеги ломают рендер), числа округляются разумно ($0.008 а не $0.00814948).

---

## Зачем

FORELDR работает на стеке из 6 сервисов (Supabase, Redis, xAI, DeepSeek, OpenRouter, fal.ai) + Railway backend + iOS app + PWA. Открывать дашборды каждые полчаса чтобы понять что в порядке — долго и неэффективно. Бот закрывает 90% операционных вопросов в Telegram за 2-3 секунды на запрос, и сам алертит когда что-то падает.

Стоимость: ~$5/мес на Railway Hobby + ~$1-2/мес на Grok-вызовы.
