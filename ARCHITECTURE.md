# Email Sanitizer / Mail Aggregator Architecture

Актуальный архитектурный документ для перехода от локального sanitizer к полноценному multi-mailbox mail aggregator.

## Цель
Построить безопасную систему, через которую агент может работать с несколькими почтовыми ящиками пользователя через CLI и backend-safe control plane.

Поддерживаемые провайдеры (целевые):
- Gmail
- Yandex
- Mail.ru
- iCloud

## Главный принцип
Агент управляет системой почты, но не владеет почтовыми секретами.

Разделение контуров:
- **Agent / CLI plane** — команды, статус, summaries, onboarding instructions
- **Secret-bearing backend plane** — OAuth/app-password flow, KMS decrypt, sync engine, raw provider IO
- **Sanitized read plane** — normalized/sanitized read model для пользователя и агента

## Слои системы
1. Agent CLI
2. Command Interpreter
3. Auth Orchestrator
4. Provider Connectors
5. Secret / KMS Layer
6. Sync Engine
7. Unified Mail Store / Read Model
8. Observability / Audit / Security Controls

## Реализационные блоки ближайшего этапа
1. Multi-mailbox config/runtime layer
2. Provider presets
3. Aggregated runner
4. Mailbox onboarding contract

## Доменные сущности (план)
- ConnectedMailbox
- MailboxCredentialRef
- MailboxSecretEnvelope
- OAuthAuthorizationSession
- SyncCheckpoint
- MailFolderState
- UnifiedMessage
- ProviderAccountCapability
- MailboxConnectionHealth

## Multi-mailbox runtime model
Каждый mailbox должен иметь:
- provider
- mailbox id
- mailbox config
- mailbox-specific secret binding
- mailbox-specific state store
- mailbox-specific sync/health state
- mailbox-specific rules/policy

Поверх этого нужен aggregate runtime, который:
- знает все enabled mailbox runtime
- умеет fan-out sync/read по всем mailbox
- агрегирует partial success
- собирает unified inbox view

## Provider strategy
### Gmail
- основной путь: OAuth 2.0
- поддержка abstraction для IMAP XOAUTH2 сейчас и Gmail API позже

### Yandex
- основной путь: OAuth
- fallback path: app password / external password if needed
- учитывать включённость IMAP

### Mail.ru
- внешний пароль приложения
- IMAP/SMTP over TLS
- учитывать выключенный внешний доступ

### iCloud
- app-specific password
- IMAP/SMTP over TLS
- не использовать основной пароль Apple ID

## Безопасность
- Никаких plaintext secrets
- Envelope encryption via KMS
- CLI не получает refresh token/app password
- Secret decrypt разрешён только backend sync/auth path
- Access token не хранится как долгоживущий секрет
- Secret values не попадают в logs/traces/metrics/errors
- Raw emails не должны попадать в agent-facing path без sanitizer/policy

## Sync model
- Инкрементальная синхронизация
- Checkpoint per mailbox + per folder
- Один mailbox не синхронизируется двумя воркерами одновременно
- Ошибка одного mailbox не валит остальные
- Partial success обязателен
- Provider-side seen state и local processed state живут отдельно и синхронизируются по policy

## CLI target capabilities
Команды целевого уровня:
- mailbox connect <provider>
- mailbox auth complete ...
- mailbox list
- mailbox status
- mailbox disconnect --mailbox-id ...
- mailbox reauth --mailbox-id ...
- mailbox sync --mailbox-id ...
- mailbox sync-all
- mailbox read --mailbox-id ...
- mailbox read-all --folder inbox --limit N
- mailbox search --query ...
- mailbox tail --unified
- mailbox health

## Что уже реализовано
- sanitizer pipeline
- prompt-injection / auth-risk detection
- mailbox-level pipeline
- config loading
- env merge
- secret naming scaffold
- state store
- runtime loader
- live IMAP scaffolding
- validation/diagnostics CLI

## Что ещё не завершено
- полноценный multi-mailbox aggregate runtime
- provider presets and onboarding flows
- mailbox onboarding contract and state machine storage
- delivery bridge to real user-facing alerting
- production-grade secrets integration

## Следующий шаг реализации
1. Ввести multi-mailbox config/runtime layer
2. Ввести provider presets и provider metadata
3. Ввести multi-mailbox aggregate runtime / runner
4. Ввести onboarding contracts (connect/auth complete/reconnect)
5. Встроить это в CLI/diagnostics

## Provider presets (implemented baseline)
Введён отдельный слой provider presets с целевыми профилями для:
- Gmail
- Yandex
- Mail.ru
- iCloud

Preset должен задавать:
- provider id
- display name
- IMAP host/port
- SSL default
- preferred auth mode
- allowed auth modes
- onboarding hints

## Aggregated runner (implemented baseline)
Введён baseline aggregated runner поверх multi-mailbox runtime.

Он уже умеет:
- fan-out по enabled mailbox
- per-mailbox isolation
- partial success contract
- aggregate notifications
- unified message projection

## Mailbox onboarding contract (implemented baseline)
Введён baseline onboarding слой для lifecycle команд:
- connect
- auth complete
- reauth
- disconnect

В нём уже есть:
- mailbox states
- connected mailbox DTO
- credential ref DTO
- OAuth authorization session DTO
- onboarding instructions
- локальный onboarding CLI
