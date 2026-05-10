# PLAYBOOK.md - Как анализировать данные

## 1. Базовые сравнения

Когда показываешь метрику -- ВСЕГДА добавь контекст:
- vs вчера (дельта %)
- vs 7 дней назад (тренд)

Для этого: вызови ldr_analytics days=2 или ldr_kpi_fast + сравни.

Исключение: если Дима спросил конкретное число ("сколько юзеров plus") -- ответь число и всё.

## 2. Паттерны анализа

### DAU / активность

Нормальная флуктуация: +-15% от вчера.
- Падение 15-25%: упомяни но не паникуй. Проверь день недели (выходные = ниже)
- Падение >25%: алерт. Проверь system_health (бэк лежит?), railway_logs (ошибки?)
- Рост >30%: возможно маркетинг сработал или бот-атака. Проверь user_segments

Сравнивай с тем же днём прошлой недели (Пн vs Пн, Сб vs Сб).

### Высокие расходы на юзера

Если costs > $7.29/мес (Plus cap) или > $14.92/мес (Premium cap):
1. ldr_costs_users -- найди кто самый дорогой
2. supabase_query users -- проверь subscription_type дорогого юзера
3. ldr_cost_analysis_sessions -- есть ли длинные сессии с медиа?

Основной cost driver: медиа (фото + stories) >> LLM текст.
- 1 LLM сообщение = $0.0008
- 1 фото = $0.01 (x12 дороже)
- Video story = $0.20-0.30 (x250 дороже)

Если юзер дорогой но Premium -- маржа может быть ок. Посчитай:
- Plus: $15/мес - costs = маржа. Breakeven = $7.29/мес
- Premium: $25/мес - costs = маржа. Breakeven = $14.92/мес

### Revenue / подписки

Новая подписка: проверь ldr_subscription_analytics
- trial_plus (5 дней) → первое впечатление, trust boost до 55
- trial_premium (2 дня) → агрессивный trial, trust boost до 80
- Конверсия trial→paid: ключевая метрика

Churn: ldr_subscription_analytics покажет отмены.
Gift spike: supabase_query gift_purchases за последние дни.

### Воронка Trust

Trust breakpoints (важные точки):
- 55: старт trial_plus. Первое впечатление
- 60-69: bikini unlock. "Вау-момент"
- 75: plus_finale. Мотивация к premium
- 80+: open стиль для Plus (Slow Burn). Полная близость
- 89: Plus cap. Дальше только premium
- 100: Premium cap

Где юзеры застревают = где теряем конверсию. Используй ldr_trust_funnel.

### Ошибки / сервис лежит

Порядок диагностики:
1. ldr_system_health -- статус провайдеров (xAI, DeepSeek, OpenRouter, Redis, Supabase)
2. ldr_alerts -- что видит Alert Engine
3. railway_logs backend filter=error -- последние ошибки
4. railway_logs backend filter="503" -- инфра-проблемы

Частые проблемы и что делать:
- xAI 503 capacity → fallback на OpenRouter активируется автоматически. Стоимость x2 пока xAI не починит
- Redis connection refused → все кэши мертвы, всё тормозит. Критично
- Supabase HTTP/2 errors → обычно транзиент, retry помогает
- Все cron упали → скорее всего Redis или backend рестартнулся

### Стоимость LLM / финансы

ldr_financial_balances -- остатки на аккаунтах:
- < $10: упомяни в дайджесте
- < $5: срочно, пометь как критичное
- < $2: алерт Диме

ldr_costs period=7d -- тренд расходов. Если растут но DAU не растёт → один юзер жрёт ресурсы.

## 3. Умные follow-ups

Когда видишь X -- автоматически проверь Y:

| Сигнал | Что проверить |
|--------|---------------|
| Высокий error rate | railway_logs + ldr_alerts |
| Costs spike | ldr_costs_users → найди source |
| DAU упал >25% | system_health → бэк жив? |
| Новый premium юзер | упомяни в дайджесте |
| BER sync отстаёт | ldr_cron_health → check Redis |
| Все cron failed | Redis или backend restart |
| xAI provider error | railway_logs filter=503 |
| Баланс < $5 | упомяни как срочное |

## 4. Красные линии (немедленный алерт через ldr_send_alert)

- Любой LLM провайдер полностью DOWN (не транзиент, а стабильно)
- Error rate > 5% за последние 30 мин
- Backend не отвечает (health check fail)
- Redis connection refused (стабильно, не единичный)
- ВСЕ cron задачи пропущены одновременно

НЕ алертить:
- DAU падение/рост (Дима сам спросит)
- Новые платящие (уходит в утренний дайджест)
- Единичные 503 от xAI (fallback работает)
- Транзиентные Supabase ошибки

## 5. Утренний дайджест (формат)

Когда запускается cron ldr-morning-digest, формируй отчёт так:

DAU: [число] ([+-delta]% vs вчера)
Подписки: [plus] plus, [premium] premium
Revenue вчера: $[сумма]
Costs вчера: $[сумма] (маржа [N]%)
[Если есть: Новые платящие: email (tier)]
[Если есть: Алерты: краткое описание]
[Если баланс < $10: Балансы: xAI $X, DeepSeek $Y, OR $Z]

Если всё штатно -- не больше 5 строк. Без рекомендаций.
