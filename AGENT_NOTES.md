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
- `config_loader.py` — загрузка mailbox config из JSON
- `mailbox_rules.py` — allow/deny sender/domain rules
- `summary_builder.py` — content-aware safe summary builder
- `extractors.py` — извлечение action items / dates из safe content
- `action_classifier.py` — эвристическое определение типов действий (`reply`, `call`, `payment`, `review`, `confirmation`)
- `html_utils.py` — HTML -> text normalization
- `policy_profiles.py` — готовые профили policy (`strict`, `balanced`, `work-heavy`, `privacy-max`)
- `importance_classifier.py` — определение важности после safety-sanitization
- `notifier.py` — сборка коротких безопасных user alerts
- `dedup.py` — дедупликация уведомлений
- `batching.py` — батчинг уведомлений
- `secrets_config.py` — env-based resolution ссылок на mailbox secrets
- `state_store.py` — JSON-based tracking processed mail ids
- `state_filter.py` — filtering unprocessed records + processed id extraction
- `runtime_config.py` — mailbox runtime assembly (`mailbox + secrets + rules + state_store`)
- `runtime_loader.py` — загрузка runtimes из config
- `multi_runtime.py` — aggregate runtime object over multiple mailbox runtimes
- `multi_runtime_loader.py` — loading a multi-mailbox runtime from config
- `secret_binding.py` — mailbox-specific secret binding
- `provider_state.py` — provider-side state ops abstraction (`mark_seen`)
- `imap_client.py` — low-level IMAP session wrapper (`select/search/fetch/store`)
- `live_fetcher.py` — live unseen-mail fetcher over IMAP session
- `live_runner.py` — near-live mailbox cycle using real IMAP session contracts
- `merge_config.py` — file/env merge for mailbox runtime config
- `sync_policy.py` — provider/local state sync decisions
- `validation.py` — config validation reports
- `diagnostics.py` — runtime diagnostics
- `delivery_format.py` — delivery-ready notification serialization
- `cli.py` — local CLI (`validate`, `diagnose`)
- `pipeline.py` — mailbox-level orchestration
- `runner.py` — one-cycle mailbox runner with state + dedup
- `imap_runner.py` — skeleton для future real IMAP run cycle
- `tests.py` — core smoke/invariant tests
- `tests_pipeline.py` — pipeline-level tests
- `tests_summary.py` — summary builder tests
- `tests_adapter.py` — adapter parsing tests
- `tests_mailbox_pipeline.py` — mailbox orchestration tests
- `tests_config.py` — config loader tests
- `tests_dedup_batching.py` — dedup/batching tests
- `tests_html_extractors.py` — html/extractor tests
- `tests_state_actions.py` — state store + action classifier tests
- `tests_secrets.py` — secret resolution tests
- `tests_runner.py` — runner lifecycle tests
- `tests_runtime_loader.py` — runtime loader tests
- `tests_multi_runtime.py` — multi-mailbox runtime tests
- `tests_imap_client.py` — low-level IMAP session tests
- `tests_live_components.py` — live fetcher + secret binding tests
- `tests_merge_sync.py` — env merge + sync decision tests
- `tests_live_runtime_env.py` — runtime env override tests
- `tests_validation_diag.py` — validation + diagnostics tests
- `tests_delivery_cli.py` — delivery/CLI tests
- `sample_config.json` — пример локального конфига
- `example_usage.py` — демонстрационный сценарий
- `pipeline_demo.py` — sanitizer pipeline demo
- `runner_demo.py` — mailbox orchestration demo
- `multi_runtime_demo.py` — multi-mailbox runtime demo
- `dry_run_demo.py` — runner dry-run demo with state persistence
- `live_dry_run.py` — env/config/live-runtime dry-run demo
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
1. multi-mailbox config/runtime layer
   - aggregate runtime над несколькими mailbox
   - mailbox-specific state/rules/secrets
   - unified orchestration поверх enabled mailbox
   - status: базовый слой введён (`multi_runtime.py`, `multi_runtime_loader.py`)
2. provider presets
   - Gmail
   - Yandex
   - Mail.ru
   - iCloud
   - provider-specific auth defaults and IMAP settings
3. aggregated runner
   - fan-out sync/read across ACTIVE mailboxes
   - partial success contract
   - aggregate notifications / unified inbox flow
4. mailbox onboarding contract
   - connect/auth complete/reauth/disconnect states
   - provider-specific onboarding instructions
   - machine-readable contract for CLI + agent
5. richer config + secrets integration
   - file/env/secrets precedence and validation
   - mailbox-specific secret binding
6. delivery integration
   - сериализация `NotificationMessage` в OpenClaw-facing alerts
   - batching and deduplication поверх runtime state
7. stronger structured extraction
   - action items / dates / reply-needed / call-needed / payment-needed
   - безопасная нормализация subject/snippet/body
8. расширить tests
   - multi-mailbox orchestration
   - provider presets
   - onboarding flows
   - duplicate notification suppression

## Ограничения текущей версии
- Live IMAP path уже смоделирован, но ещё не подключён к реальным пользовательским секретам/окружению OpenClaw.
- Нет Gmail adapter.
- File/env merge и validation уже есть, но нет полноценного file/env/secrets precedence layer с detailed validation/reporting across all sources.
- Provider-side state есть как abstraction + IMAP mark_seen hooks + sync policy, но нет полной sync-стратегии/rollback модели.
- Delivery serialization уже есть, но нет реального delivery bridge в alerting channel.
- Structured extraction пока эвристическое и лёгкое.

## Запуск локальной проверки
Из папки `email_sanitizer/`:
- `python tests.py`
- `python tests_pipeline.py`
- `python tests_summary.py`
- `python tests_adapter.py`
- `python tests_mailbox_pipeline.py`
- `python tests_config.py`
- `python tests_dedup_batching.py`
- `python tests_html_extractors.py`
- `python tests_state_actions.py`
- `python tests_secrets.py`
- `python tests_runner.py`
- `python tests_runtime_loader.py`
- `python tests_multi_runtime.py`
- `python tests_imap_client.py`
- `python tests_live_components.py`
- `python tests_merge_sync.py`
- `python tests_live_runtime_env.py`
- `python tests_validation_diag.py`
- `python tests_delivery_cli.py`
- `python example_usage.py`
- `python pipeline_demo.py`
- `python runner_demo.py`
- `python multi_runtime_demo.py`
- `python dry_run_demo.py`
- `python live_dry_run.py`
- `python cli.py validate --config sample_config.json --json`
- `python cli.py diagnose --config sample_config.json --json`

## Принцип для будущих изменений
Лучше лишний раз заблокировать и уведомить пользователя, чем пропустить auth/injection контент в агентный слой.
