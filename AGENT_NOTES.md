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
- `tests.py` — smoke/invariant tests
- `example_usage.py` — демонстрационный сценарий
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
1. `mail_fetcher.py`
   - IMAP / Gmail ingestion
   - fetch metadata/snippet/body locally
   - raw письма не отдавать наружу
2. `policy_profiles.py`
   - strict
   - balanced
   - work-heavy
   - privacy-max
3. `importance_classifier.py`
   - определять, что реально важно пользователю
   - учитывать sender/domain/category/urgency
4. `notifier.py`
   - собирать короткие безопасные user alerts
5. расширить tests:
   - magic links
   - shorteners
   - bank/security emails
   - medical appointment vs medical results
   - work emails with harmless links

## Ограничения текущей версии
- Нет реального mail ingestion.
- Нет persistent policy config.
- Нет allowlist/denylist sender/domain rules.
- Нет importance scoring поверх safety.
- Summary пока шаблонный, а не content-aware.

## Запуск локальной проверки
Из папки `email_sanitizer/`:
- `python tests.py`
- `python example_usage.py`

## Принцип для будущих изменений
Лучше лишний раз заблокировать и уведомить пользователя, чем пропустить auth/injection контент в агентный слой.
