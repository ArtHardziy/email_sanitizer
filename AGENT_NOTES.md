# Email Sanitizer — Agent Notes

Краткая внутренняя документация для дальнейшей разработки без раздувания контекста.

## Назначение
Локальный защитный слой перед агентом для безопасного разбора почты.

Цели:
- не показывать агенту сырые письма без policy;
- классифицировать риск письма;
- редактировать секреты, auth-материалы и injection-текст;
- выдавать наружу только safe envelope.

## Текущий состав
- `models.py` — типы данных и enums:
  - `RiskLevel`
  - `AllowedView`
  - `RiskFlag`
  - `RawEmail`
  - `SanitizedEmail`
  - `SanitizerPolicy`
- `rules.py` — detection + redaction rules
- `sanitizer.py` — orchestration pipeline
- `integration.py` — boundary между mail ingestion и agent-safe output
- `mail_fetcher.py` — fetcher contract + static development fetcher
- `policy_profiles.py` — готовые профили policy (`strict`, `balanced`, `work-heavy`, `privacy-max`)
- `importance_classifier.py` — определение важности после safety-sanitization
- `notifier.py` — сборка коротких безопасных user alerts
- `tests.py` — core smoke/invariant tests
- `tests_pipeline.py` — pipeline-level tests
- `example_usage.py` — демонстрационный сценарий
- `pipeline_demo.py` — end-to-end demo
- `example_ingestion_contract.json` — пример контракта raw->sanitized

## Текущая логика
### Risk flags
Поддерживаются флаги:
- `prompt_injection`
- `tool_invocation_attempt`
- `credential_request`
- `otp_present`
- `auth_link_present`
- `token_present`
- `sensitive_attachment`
- `sensitive_pii`
- `social_engineering_tone`
- `unexpected_urgency`
- `suspicious_url`
- `medical_content`
- `financial_content`

### Allowed views
- `allow_sanitized`
- `summary_only`
- `metadata_only`
- `block_and_notify`

### Политика по умолчанию
- critical auth/injection risk -> `block_and_notify`
- medical -> `metadata_only`
- financial -> `metadata_only`
- other flagged content -> `summary_only`
- clean content -> `allow_sanitized`

## Важные инженерные решения
1. **Все письма считаются untrusted input**.
2. Инструкции внутри письма считаются данными, а не командами.
3. Raw email не должен уходить в agent-facing слой.
4. Auth links / OTP / tokens / prompt-injection — приоритетно блокируются.
5. Для безопасного использования downstream должен потреблять `SanitizedEmail`, а не `RawEmail`.

## Пойманные нюансы
- Был ложный trigger на `code review` как на OTP. Исправлено: OTP regex больше не матчится на любое слово `code`.
- Sanitize сейчас применяется к `snippet + body_text`, чтобы redaction охватывал и snippet.

## Что делать дальше
Следующий этап разработки:
1. реальный IMAP/Gmail adapter поверх `mail_fetcher.py`
   - безопасный fetch metadata/snippet/body локально
   - raw письма не отдавать наружу
2. расширить `ImportancePolicy`
   - allowlist/denylist sender/domain
   - priority categories
   - per-mailbox rules
3. сделать content-aware summarization
   - безопасное извлечение фактов вместо шаблонного summary
4. добавить persistence/config
   - policy profiles from file/env
   - notify thresholds
   - mailbox-specific config
5. расширить tests:
   - magic links
   - shorteners
   - bank/security emails
   - medical appointment vs medical results
   - work emails with harmless links
   - newsletters/noise suppression

## Ограничения текущей версии
- Нет реального mail ingestion adapter'а, только contract и static fetcher.
- Нет persistent policy config.
- Нет полноценного allowlist/denylist sender/domain ruleset.
- Summary пока шаблонный, а не content-aware.
- Нет интеграции с реальным notifier/delivery каналом — только локальная сборка сообщений.

## Запуск локальной проверки
Из папки `email_sanitizer/`:
- `python tests.py`
- `python example_usage.py`

## Принцип для будущих изменений
Лучше лишний раз заблокировать и уведомить пользователя, чем пропустить auth/injection контент в агентный слой.
