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
- `imap_adapter.py` — thin IMAP adapter + `.eml` parsing helper
- `config.py` — mailbox/app config models
- `mailbox_rules.py` — allow/deny sender/domain rules
- `summary_builder.py` — content-aware safe summary builder
- `policy_profiles.py` — готовые профили policy (`strict`, `balanced`, `work-heavy`, `privacy-max`)
- `importance_classifier.py` — определение важности после safety-sanitization
- `notifier.py` — сборка коротких безопасных user alerts
- `pipeline.py` — mailbox-level orchestration
- `tests.py` — core smoke/invariant tests
- `tests_pipeline.py` — pipeline-level tests
- `tests_summary.py` — summary builder tests
- `tests_adapter.py` — adapter parsing tests
- `tests_mailbox_pipeline.py` — mailbox orchestration tests
- `example_usage.py` — демонстрационный сценарий
- `pipeline_demo.py` — sanitizer pipeline demo
- `runner_demo.py` — mailbox orchestration demo
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
1. реальный credential-aware IMAP/Gmail adapter
   - локальная загрузка секретов/токенов вне agent-facing path
   - безопасный fetch unseen/new mail
   - маркировка processed/read state
2. persistence/config loading
   - mailbox config из file/env/secrets
   - policy profile selection per mailbox
   - notify thresholds and schedules
3. richer allow/deny and categorization
   - sender/domain/category allowlists
   - noisy sender suppression
   - per-mailbox overrides
4. stronger summaries
   - лучшее извлечение action items / dates / urgency
   - безопасная нормализация subject/snippet/body
5. delivery integration
   - сериализация `NotificationMessage` в OpenClaw-facing alerts
   - batching and deduplication
6. расширить tests:
   - multipart emails
   - html-only emails
   - encoded headers
   - newsletters/noise suppression
   - sender deny + security override conflicts

## Ограничения текущей версии
- IMAP adapter пока intentionally incomplete: нет реального login flow и работы с секретами.
- Нет Gmail adapter.
- Нет persistent config loading из файлов/env.
- Нет delivery integration в реальный alerting channel.
- Content-aware summary пока лёгкий эвристический, не извлекает action items структурно.

## Запуск локальной проверки
Из папки `email_sanitizer/`:
- `python tests.py`
- `python example_usage.py`

## Принцип для будущих изменений
Лучше лишний раз заблокировать и уведомить пользователя, чем пропустить auth/injection контент в агентный слой.
