# Дослідження ринку та архітектури для комерційного hosted MCP-сервера з векторною пам’яттю і ієрархічними задачами

## Executive summary

Станом на 2025–2026 роки MCP швидко перетворився з “корисного протоколу” на базовий шар інтероперабельності для агентних систем: у грудні 2025 MCP був формально переданий до новоствореного **Agentic AI Foundation** під парасолькою **Linux Foundation**, із публічним акцентом на “нейтральність, відкритість та ком’юніті‑керованість” — це ознака довгого горизонту життя стандарту та його інституційного закріплення. citeturn27search0turn27search1turn27search2

Ключовий технічний зсув у MCP за 2025 рік — стандартизація **Streamable HTTP transport** як “один HTTP endpoint” (GET для стріму/подій, POST для запитів), з уточненнями безпеки та поведінки з’єднань у редакціях 2025‑03‑26 та 2025‑11‑25. Це критично саме для вашого задуму “один комерційний hosted endpoint”. citeturn2view0turn2view1

Паралельно протокол еволюціонує до “production gap” фіч: у редакції 2025‑11‑25 з’явився **Tasks** (експериментальний) як протокольний примітив для довгих операцій із polling та відкладеним отриманням результатів. Це прямо резонує з вашим “Vector Task MCP” (паралельне виконання/довгі операції) і дає шлях до стандартного UX у клієнтах, але ризик — “experimental” статус. citeturn18view0turn18view1

Ринок “комерційних MCP серверів” фрагментований: з одного боку — **hosted MCP у великих SaaS‑платформах** (Notion, Linear, Atlassian, Sentry), де MCP — це “міст” до їхніх даних із OAuth і політиками доступу; з іншого — **MCP hosting / deployment платформи**, які продають хостинг, авторизацію, аналітику та/або “швидкий старт” для MCP. Це означає, що попит на hosted MCP уже підтверджений, але ваша диференціація має бути не “ще один MCP сервер”, а **шар стану агентів**: *semantic memory + task state + workflow primitives* з multi‑tenancy та ліцензуванням. citeturn21view0turn21view1turn21view2turn35view1turn34view1turn34view2

Технічно головна причина, чому ваші локальні SQLite‑базовані MCP‑сервери “не тягнуть” multi‑agent concurrency, — фундаментальна модель SQLite: навіть у WAL режимі одночасно можливий лише **один writer** (при багатьох readers), що створює lock contention під паралельними агентами. Перехід на мережеву СУБД або винесення writer‑шляху в чергу — практично неминучий. citeturn6search0

Рекомендована “продуктова” стратегія: **hybrid** (Cloud SaaS + self-hosted Docker) із чітко розділеними SKU, як це роблять успішні dev‑tools (приклади: Sentry (cloud + self-host), Supabase (cloud + self-host), GitLab (open core)). citeturn15search4turn15search2turn15search16

## Market & competition

Комерційний ландшафт навколо MCP у 2025–2026 логічно розбивається на три категорії: (а) **“дані як MCP” від великих SaaS**, (б) **інструментальні dev‑платформи (observability / dev workflow) з MCP‑конектором**, (в) **MCP hosting / infra сервіси**, які продають “endpoint, auth, аналітику, домени, SLA”.

### Hosted MCP у великих SaaS платформах (де MCP — це “вхід у їхній продукт”)

Notion позиціонує Notion MCP як “hosted сервер, який дає AI‑інструментам безпечний доступ до workspace”, підкреслює простий OAuth‑онбординг та “AI‑оптимізоване форматування”, і прямо описує use-cases “docs + search + manage tasks”. Це важливо: Notion продає не протокол, а **AI‑інтеграцію робочого простору**. citeturn21view0

Linear публікує “Remote MCP server” як стандартизований, “simple and secure” доступ до даних Linear, наголошує, що сервер “centrally hosted and managed” та підтримує і SSE, і Streamable HTTP; окремо рекомендує Streamable HTTP “for increased reliability”, а auth будує на OAuth 2.1 (із dynamic client registration). Це хороший референс “як виглядає production hosted MCP”. citeturn21view1

Atlassian у рамках Rovo MCP server позиціонує рішення як “integration layer”, яка дає структурований пошук і fetch доступ з зовнішніх AI клієнтів з OAuth та гранулярними правами; окремо заявляє, що MCP server **не зберігає і не кешує** Jira/Confluence контент — працює як secure proxy, і публікує rate limits, прив’язані до планів Jira/Confluence (Free/Standard/Premium/Enterprise). Це демонструє enterprise‑практику: *мінімізація зберігання*, *гардрейли*, *ліміти*. citeturn21view2

У підсумку: “hosted MCP” уже став конкурентним полем, але ці приклади — **одно‑джерельні конектори**. Ваш шанс — стати “станом агентів” над багатьма джерелами, а не “ще одним конектором до X”.

### Dev‑tools з MCP вбудовуванням (observability та “production feedback loop”)

Sentry має remote MCP‑сервер (open-source репозиторій), який прямо описує як middleware до upstream Sentry API, оптимізований для coding assistants. Важлива деталь для вашого продукту: Sentry відкрито підкреслює, що їхній MCP — **не general-purpose**, а фокус на “human‑in‑the‑loop coding agents” та debugging flows. Це означає: MCP часто монетизують не як “endpoint”, а як **частину платформи цінності** (observability/інциденти/виправлення). citeturn35view1

### MCP hosting / “endpoint-as-a-service” (з продажем auth, аналітики, доменів, SLA)

Цей сегмент молодий і волатильний, але показовий: він валідуює попит на hosted endpoint із вбудованими “enterprise knobs”.

Hypr MCP явно продає “enterprise-grade MCP servers with authentication, analytics, and advanced security” з тарифами: free (1k requests/mo), pro ($69/mo, 100k requests included, custom domains, 99.9% SLA), enterprise (dedicated infra, SOC 2 тощо). Це практично “проксі” вашого майбутнього ціннісного пакету, але без вашої “memory+tasks” диференціації. citeturn34view1

MCP-Builder.ai продає “Fully Hosted HTTP-Streamable MCP-Server” з Pro $30/mo і Scale $225/mo, включаючи security connectors, вибір моделі тощо. Це сигнал, що на ринку вже формується очікування: “MCP сервер = hosted сервіс + auth + UI + модель/LLM інтеграція”. citeturn34view2

Smithery (за результатами пошуку) також позиціонується як інфраструктура для MCP з керуванням OAuth/секретами; ціни вказані на сторінці pricing у видачі пошуку (сам сайт блокує прямий перегляд). Це треба врахувати як конкурента “інфраструктурного шару”. citeturn1search1

Окремо існують “MCP hosting для індивідуалів” (наприклад, mcpfy.ai) з дуже простими тарифами; у видачі пошуку mcpfy.ai показує $10/mo для starter. Цей сегмент, імовірно, змагається за “хобі/інді” та може задавати очікування “дешевий endpoint”. citeturn33search2

### Конкурентна матриця (скорочена)

| Категорія | Приклад | Що продає | Auth/тенантність | Наявність “пам’яті”/“задач” як продукту | Модель монетизації (публічно) |
|---|---|---|---|---|---|
| SaaS‑дані через MCP | Notion | Доступ AI до workspace + use-cases (docs/search/tasks) | OAuth, “secure access” | Ні (це міст до Notion data) | Не відокремлено як MCP‑тариф citeturn21view0 |
| Task/project SaaS через MCP | Linear | Доступ AI до issues/projects/comments; remote server | OAuth 2.1; Streamable HTTP рекомендований | Ні (це міст до Linear) | Не відокремлено як MCP‑тариф citeturn21view1 |
| Enterprise knowledge SaaS MCP proxy | Atlassian (Rovo) | “Integration layer”, search/fetch, проксі до Jira/Confluence | OAuth; rate limits за планами; не кешує дані | Ні (наголос на proxy) | Вбудовано в Atlassian Cloud (ліміти по планах) citeturn21view2 |
| Dev observability MCP | Sentry | Debugging контекст для coding assistants | Залежить від конфігурації; remote + stdio | Ні, але є “контекст інцидентів” | Вбудовано в Sentry екосистему citeturn35view1 |
| MCP hosting (infra) | Hypr MCP | Endpoint + auth + аналітика + SLA | OAuth2; enterprise security | Немає доменної “memory/tasks” | Free → $69/mo → Enterprise citeturn34view1 |
| MCP builder/hosted platform | MCP-Builder.ai | Hosted Streamable HTTP MCP + security connectors | Є | Немає окремо “memory/tasks” | Free → $30/mo → $225/mo → Enterprise citeturn34view2 |
| Agent memory SaaS | Mem0 | “Memory layer” + retrieval API | Платформні features (SSO/audit в enterprise) | Пам’ять — так; задачі — ні | Free → $19/mo → $249/mo → Enterprise citeturn30view0 |
| Agent memory / context engineering SaaS | Zep | Agent memory / GraphRAG / context engineering | Enterprise варіанти деплою, compliance | Пам’ять — так; задачі — ні | Кредит‑модель + enterprise опції citeturn28view2 |
| Stateful agents platform | Letta | Stateful agents, BYOK, remote MCP tools | Enterprise з RBAC/SSO | Пам’ять — так; задачі — частково через агентів | Free → $20/mo → $200/mo → Enterprise citeturn30view1 |

### TAM і платоспроможність аудиторії (практична оцінка)

Для “AI developer tooling із MCP інтеграцією” TAM краще оцінювати не як “ринок MCP”, а як **підмножину ринку AI‑підсиленої розробки + agent infrastructure**.

Орієнтири по базі користувачів: JetBrains оцінює кількість *професійних* розробників у світі на 2025 рік приблизно у 20.8 млн. citeturn10search0 GitHub у Octoverse 2025 показує “over 180 million developers” (це скоріше accounts, не лише професійні), що важливо для верхньої межі топ‑воронки. citeturn10search2

За цінами на сучасні AI dev‑tools видно готовність платити $10–$40/міс на індивідуальному рівні та $19–$40/seat/mіс на командному рівні (наприклад, Copilot Business $19/seat/mіс; Cursor Teams $40/юзер/міс; індивідуальні плани Cursor $20/міс). citeturn16search0turn28view1

Отже практичний “serviceable TAM” для вашого продукту (hosted state layer для агентів) доцільно моделювати як:
- **інтеграційно‑активні команди** (де вже є MCP клієнт типу IDE/agent harness) ×
- **потреба у довгостроковій пам’яті + task state** ×
- **готовність платити за інфраструктуру**, близька до “dev‑tool subscription”.

Навіть при консервативній частці 2–5% від ~20.8 млн професійних девів (тобто ~0.4–1.0 млн потенційних платних користувачів), при ARPU $15–$40/міс, виходить орієнтовний порядок **$70M–$480M ARR** як довгий верхній коридор (це модель‑оцінка, не факт). Підтвердженням масштабу тенденції є те, що незалежні аналітичні звіти вже оцінюють “generative AI in software development” як десятки мільярдів доларів на рік у середині 2020‑х (але це дуже широка категорія, що включає багато підринків). citeturn10search3

## Technical architecture recommendations

### MCP transport: Streamable HTTP як “основа продукту”

Streamable HTTP transport у MCP формалізує модель “один endpoint”, який підтримує POST (JSON-RPC запити/відповіді) та GET (стрім повідомлень, зокрема через SSE). Саме це відповідає вашій вимозі “single HTTP/SSE endpoint”. citeturn2view0turn2view1

Важливо, що “production‑підтвердження” Streamable HTTP видно не лише в специфікації, а й у тому, як його використовують великі продукти: Linear підтримує SSE та Streamable HTTP і рекомендує Streamable HTTP як більш надійний варіант; також використовує OAuth 2.1. citeturn21view1

З боку клієнтів, Codex документує підтримку “Streamable HTTP servers” із Bearer token та OAuth‑логіном, включно з конфігураційними полями під `Authorization` header (bearer_token_env_var) та іншими HTTP headers. Це означає: якщо ваш hosted MCP endpoint підтримує стандартні патерни auth, у вас є “ready client surface” у реальних dev‑інструментах. citeturn37view0

### Tasks primitive: як “стандартний API” для довгих операцій (але з ризиком)

MCP Tasks з’явилися у ревізії 2025‑11‑25 і прямо описані як “durable state machines” для polling та deferred result retrieval; при цьому Tasks **експериментальні** і можуть змінюватися. citeturn18view0turn18view1

Для вашого продукту Tasks — ключ до стандартизації таких операцій як: bulk‑embedding, переіндексація, масове оновлення тегів/IDF, long‑running workflow над задачами, “планування/перепланування” великого дерева задач. Але через experimental‑статус найкраща практика — реалізувати Tasks як **додатковий шар**, паралельно залишивши синхронний API для MVP, щоб не прив’язуватися до можливих змін протоколу. citeturn18view0turn18view1

### AuthN/AuthZ: сумісність зі специфікацією і мінімальний шлях до MVP

Специфікація 2025‑11‑25 формалізує MCP Authorization як підмножину OAuth 2.1: MCP server виступає як OAuth resource server, клієнт — як OAuth client; сервери MUSТ реалізувати OAuth Protected Resource Metadata (RFC 9728), клієнти MUSТ використовувати цей механізм для discovery; також описані правила token validation, audience, і важлива заборона token passthrough (щоб уникати confused deputy). citeturn19view0

Окремо Security Best Practices жорстко попереджають: **не використовувати session як auth**, перевіряти inbound requests, робити session IDs крипто‑рандомними, і розглядати ризики session hijack/event injection. Для multi‑tenant hosted сервера це означає: session_id може існувати як транспортний ідентифікатор, але **авторизація має бути прив’язана до токена/ключа** й перевірятись на кожний запит. citeturn19view1

Практичний компроміс для “швидкого MVP, але без стратегічного боргу”:
- **MVP**: API keys як Bearer token у `Authorization` (це добре лягає на “bearer token authentication” у клієнтах на кшталт Codex). citeturn37view0  
- **Roadmap**: перехід/додавання повністю spec‑compliant OAuth 2.1 discovery + flows (щоб працювати “нативно” у клієнтських UI інтеграційних галереях, як у великих SaaS).

### Persistent storage: чому SQLite треба замінити, і що вибрати

Ваша проблема з конкурентним доступом у SQLite не випадкова: навіть у WAL режимі SQLite дозволяє читачам і writers працювати паралельно, але **writer може бути тільки один** (один WAL файл → один writer), що при multi‑agent write‑нагрузці спрацьовує як bottleneck. citeturn6search0

Отже hosted‑продукт майже неминуче має перейти на:
- мережеву транзакційну СУБД (часто — PostgreSQL),
- або окремий write‑сервіс із чергою/батчингом,
- або спеціалізовану vector DB + окремий relational store для бізнес‑таблиць.

### Vector store вибір: PostgreSQL+pgvector vs спеціалізовані vector DB

**PostgreSQL + pgvector**. pgvector підтримує exact search за замовчуванням, а для ANNS — індекси HNSW та IVFFlat. Це дозволяє мати один datastore для tasks, licensing, audit logs і векторів — сильно спрощує multi‑tenant і self‑hosted story. citeturn5search0

**Qdrant**. Qdrant у документації прямо рекомендує multi‑tenancy як “одна колекція на embedding model + payload‑based partitioning” у більшості випадків (тобто tenant_id в payload + фільтри). Це хороший шлях для hosted SaaS при великій кількості дрібних tenants. citeturn5search1 Також Qdrant розвиває “tiered multitenancy” (під різні профілі tenants), що сигналізує зрілість multi‑tenant сценаріїв. citeturn5search17

**Weaviate**. Weaviate документує multi‑tenancy як “data isolation”, де кожен tenant зберігається на окремому shard і невидимий іншим. Це привабливо для сильнішої ізоляції, але може збільшувати управлінську складність/ресурсний профіль. citeturn5search2

**Milvus**. Milvus описує multi‑tenancy як набір стратегій і прямо фіксує “partition-level multi-tenancy” з лімітом до 1024 partitions на колекцію (як приклад). Це корисно, якщо ви будуєте “великий shared кластер”, але потрібно проектувати межі tenant‑кількості та resource isolation. citeturn5search3

**Комерційний сигнал pricing’у**: у керованих vector DB вже нормалізувались free tiers та мінімальні місячні чеки для production: Qdrant має “Managed Cloud starting at $0” з 1GB free cluster; Pinecone має free Starter і “Standard $50/month min usage”, “Enterprise $500/month min usage”; Weaviate має $30/organization (для Query Agent) як окремий комерційний модуль. citeturn28view3turn31view0turn30view3

#### Рекомендація по векторному шару для вашого продукту

Для першого комерційного релізу (із вимогою “Docker + hosted”) найчастіше перемагає **PostgreSQL + pgvector** як default:
- єдиний datastore → менше компонентів у self‑hosted,
- зрілий multi‑tenant підхід через tenant_id + RLS,
- транзакційність для task workflows і licensing.

А для higher tiers / enterprise можна дати “pluggable vector backend”: Qdrant/Weaviate/Milvus як опція (особливо коли потрібні окремі профілі tenants, shard‑ізоляція, або коли вектори переростають у десятки/сотні мільйонів).

### Multi-tenancy patterns: shared DB vs schema‑per‑tenant vs DB‑per‑tenant

Якщо базовий store — PostgreSQL, то RLS є “канонічним” інструментом для row‑level ізоляції: `CREATE POLICY` визначає політики доступу, які застосовуються тільки після `ENABLE ROW LEVEL SECURITY`. Це дає defense‑in‑depth на рівні БД. citeturn22search3turn22search7

На рівні продукту найчастіше виграє гібридна схема:
- **Shared DB (tenant_id + RLS)** для Free/Pro/Business: дешевше, простіше, легше масштабувати дрібні tenants.
- **Schema‑per‑tenant або DB‑per‑tenant** для Enterprise (або “Dedicated cluster”): легше гарантувати data residency/ізоляцію, простіше пояснювати compliance.

Для vector DB multi‑tenancy практики теж різняться (payload partitioning у Qdrant; shard‑per‑tenant у Weaviate; partitions у Milvus). Це створює природну точку для “enterprise upgrade”: окремий backend/кластер або окрема стратегія multi‑tenancy. citeturn5search1turn5search2turn5search3

### Go vs Python для висококонкурентного MCP HTTP сервера

У 2026 MCP екосистема має “офіційні SDK” у багатьох мовах; Go SDK існує офіційно, і MCP docs показують Go як один із SDK, а також вказують, що офіційні SDK tiers мають бути опубліковані 23 лютого 2026 (тобто протокол і SDK‑екосистема ще активно формалізуються). citeturn36view0 Також є офіційний репозиторій go-sdk. citeturn4search0turn4search6

З огляду на ваші вимоги (SSE/стріми, багато одночасних агентів, multi‑tenant auth, rate limits) Go часто буде більш “прямим” вибором як gateway‑сервіс. Python може бути достатнім при правильному async стеку + горизонтальному масштабуванні, але тоді вам треба дуже дисципліновано зробити:
- process model (кілька воркерів),
- connection pooling,
- backpressure для SSE,
- і фонова робота через queue.

**Рекомендована компромісна архітектура**: Go як MCP gateway (transport+auth+rate limiting), а “domain ядро” (embedding, normalization, IDF, планувальник задач) може бути окремим сервісом (Go або Python) — залежно від того, що ви хочете пере‑використати з ваших існуючих Python‑MCP серверів.

### Embeddings: in-process vs external APIs vs inference server

Ви використовуєте all‑MiniLM‑L6‑v2 із 384‑вимірними ембедінгами (це прямо вказано на model card). citeturn14search0 Для hosted‑продукту є три життєздатні режими:

1) **External embeddings API** як дефолт для SaaS (особливо на early stage), щоб уникнути GPU/інференс‑операцій. Як приклад, OpenAI публікує ціну для `text-embedding-3-small` $0.02 за 1M tokens (і batch дешевше). citeturn30view2  
2) **In-process CPU embeddings** (ONNX/transformers) для self‑hosted Docker і low‑volume SaaS tiers: дешевше в оперуванні, але потрібен контроль latency/черг.  
3) **Dedicated inference server** коли потрібна висока пропускна здатність: Triton підтримує dynamic batching для збільшення throughput; vLLM надає OpenAI‑compatible HTTP server для LLM serving (корисно, якщо ви захочете `BYOM`/self-hosted LLM або “вбудовані агентні операції”). citeturn14search2turn14search1

Найкращий продуктово‑економічний патерн: **BYOK (Bring Your Own Key)** для “LLM/embeddings provider” + optional “managed embeddings add‑on”. Паралель: Letta у free плані явно зазначає BYOK для LLM API keys. citeturn30view1

## SEO, positioning, and go-to-market

### Категорія продукту: що писати на лендингу (і чого не писати)

Назва класу “MCP server” занадто нішова і для SEO, і для продажів. Навіть великі гравці виносять MCP як “інтеграційний механізм”, а продають “secure access / integration layer / agent workflows”.

Семантичні “категорії, які продають” на основі позиціонування ринку:
- “AI agent memory” / “memory layer” — Mem0 буквально продає “AI memory” і тарифи вимірює “memories + retrieval API calls”, додаючи SSO/audit/on-prem в enterprise. citeturn30view0
- “context engineering” / “agent context” — Zep прямо використовує ці терміни як продуктові розділи і будує тарифікацію кредитами. citeturn28view2
- “agent infrastructure” / “integration layer” — Atlassian називає MCP server integration layer і акцентує безпеку/permissioning. citeturn21view2
- “hosted connector” / “secure access to workspace data” — Notion саме так і формулює. citeturn21view0

**Рекомендований клас продукту для вас**:  
“Agent Memory & Workflow Backend” або “AI Agent State Platform” (а MCP — як “інтеграційний протокол/інтерфейс”).

### Кластери ключових слів (для контент‑плану)

Замість “mcp server” цільтесь у кластери, які вже мають попит (і підводять до MCP природно):
- agent memory, long-term memory for AI agents, semantic memory, memory layer for LLMs (ринок уже вчиться цим словам через Mem0/Zep/Letta). citeturn30view0turn28view2turn30view1
- context engineering, GraphRAG, agent context store (Zep активно пушить). citeturn28view2
- agent task management, agent workflow engine, durable tasks, background jobs for agents (плюс прив’язка до MCP Tasks). citeturn18view0turn18view1
- multi-tenant vector database, pgvector multi-tenant, vector search at scale (під ваші технічні статті). citeturn5search0turn22search7
- OAuth 2.1 for agent tools, MCP authorization, token audience, confused deputy (болі безпеки вже формалізовані у MCP spec). citeturn19view0turn19view1

### Go-to-market: найкоротший шлях до PMF

Найлогічніший стартовий сегмент — **команди, які вже використовують агентні IDE/інструменти** і хочуть “пам’ять + задачі” як зовнішній persistence layer. Підтвердження платоспроможності: сучасні coding assistants мають чіткі публічні тарифні сітки для індивідів і команд (Cursor, Copilot, Claude subscriptions). citeturn28view1turn16search0turn16search2

Успішний “open-source → commercial” шаблон у dev‑tools зазвичай виглядає як:
- cloud‑продукт із generous free tier + usage‑based або seat‑based масштабування (PostHog — явна usage‑based модель; Supabase — cloud pricing + self-hosting docs; Sentry — cloud pricing + self-hosted). citeturn15search0turn15search2turn15search4
- open-core або “open core + paid tiers” як корпоративний механізм монетизації (GitLab прямо описує open core і revenue з paid tiers). citeturn15search16

## Business model and pricing

### Рекомендація: hybrid модель як “дефолт” для dev‑tools

Для dev‑інфраструктури, яку хочуть і локально (Docker), і hosted, найбільш життєздатний підхід — **hybrid**:
- Cloud SaaS для швидких команд/стартапів,
- Self-hosted ліцензія для enterprise (особливо там, де є data residency, приватні мережі, залізний compliance).  
Цей підхід узгоджується з тим, як ринок уже працює (Sentry self-hosted, Supabase self-hosting). citeturn15search4turn15search11

### Які метрики продавати (per-seat vs per-request vs per-agent)

По ринку видно 3 робочі патерни:

1) **Per-seat** (передбачувано для менеджменту, але ризик “power users” по юніт‑економіці): Copilot Business — $19/seat/mіс; Cursor Teams — $40/user/mіс. citeturn16search0turn28view1  
2) **Usage‑based** (справедливо й масштабується): PostHog показує прозору usage‑based модель по подіях/запитах. citeturn15search0  
3) **Hybrid subscription + included usage + overages**: Mem0 має Free/Starter/Pro з лімітами “memories + retrieval calls”, і enterprise включає on‑prem/SSO/audit. citeturn30view0 Hypr MCP також дає “100k requests included + overage price”. citeturn34view1

Для вашого продукту (memory+tasks) найкраща комерційна одиниця — **requests/tool calls + storage** (вектори/метадані) + “active agents/concurrency” як enterprise‑параметр. “Per-seat” варто залишити як enterprise опцію (там так купують), але не як єдину метрику.

### Пропонована тарифна сітка (конкретний варіант)

Free (для швидкого adoption)
- 1 workspace (1 tenant), 1 API key
- ліміт requests/місяць (наприклад 5k–20k)
- ліміт storage (наприклад до N “memory items”/tasks)
- базові features: vector search, task tree, мінімальний audit
- BYOK embeddings/LLM

Pro (індивідуали/інді/малий SaaS)
- 1–3 workspaces, кілька keys
- 100k–500k requests/місяць included + overages
- retention/backup базового рівня
- webhook/інтеграції
- пріоритетна підтримка

Business (команди)
- team management, ролі
- SSO (SAML/OIDC), audit logs, usage analytics
- higher limits, гарантований rate limit

Enterprise
- dedicated deployment (кластер або DB‑per‑tenant)
- data residency option
- SLA, security review, private networking
- self-hosted license + support

Ця логіка відповідає тому, що ринок уже нормалізував як “enterprise add-ons”: SSO, audit logs, dedicated infra, SLA. citeturn28view1turn30view0turn34view1

### Ліцензування та provisioning через API

Якщо ви робите self‑hosted, потрібно мати “license provisioning API” і механіку токенів/активацій. Практичний варіант — **підписані токени (JWT)** або подібна структура з key rotation/expiry, разом з server-side перевіркою та можливістю відкликання. Загальні best practices для токенів: expiration, HTTPS, і правильна валідація. citeturn25search9turn25search6

Якщо ви хочете пришвидшити time-to-market, індустріальний референс — API‑орієнтовані licensing платформи на кшталт Keygen (вимагає TLS, REST API, токени/permissions), але навіть якщо робите все інхаус, їхня модель ресурсів (keys/licenses/tokens/activations) — хороший шаблон. citeturn25search2turn25search5

Для usage‑based білінгу (cloud) стандартний підхід — metered usage, як у Stripe Billing (usage records → агрегування в кінці періоду). citeturn25search16turn25search12

## Deployment, infrastructure, and cost model

### Docker Compose: рекомендована “мінімальна” топологія

Для вашої вимоги “локально (Docker) і на сервері” найкраще проектувати **однакову базову топологію**:

- `mcp-gateway` (Streamable HTTP + SSE, auth, rate limiting)
- `core-service` (memory/tasks домен: embeddings pipeline, normalization, IDF, task workflow engine)
- `worker` (background jobs: re-embed, batch ingest, TTL cleanup, exports) — інтегрується з MCP Tasks
- `postgres` (або postgres+pgvector) як primary store
- `redis` (rate limit counters, idempotency, job queue)
- `admin-panel` (Laravel Brain): tenants, licenses/keys, usage dashboards, billing hooks

Така схема легко масштабується горизонтально для gateway і workers.

### SSE та проксі: “дрібні” настройки, які ламають production

SSE — це довге HTTP‑з’єднання. На edge/proxy шарі найчастіші проблеми: буферизація, таймаути, keepalive. Мінімальні практики:
- проксі має коректно працювати з long‑running connection (Nginx часто вимагає спеціальних proxy параметрів). citeturn24search1
- бажано слати heartbeat/коментарі як keep-alive, якщо події можуть бути рідкими (MDN прямо згадує коментар як keep-alive механізм). citeturn24search7

Для edge‑розміщення: Cloudflare документує патерни HTTP+SSE для агентів; це корисно, якщо ви думаєте про “ближче до клієнта” виконання gateway‑шару. citeturn24search0turn24search20

### Backup / disaster recovery для vector store

Якщо ви підете шляхом спеціалізованої vector DB, DR механізми мають бути частиною продукту (і продаватись як enterprise feature):
- Qdrant описує snapshots/backup і автоматичні backups у cloud UI. citeturn23search8turn23search12
- Weaviate документує backups та підкреслює, що локальні backups не підходять для production; для production рекомендовані S3/GCS/Azure Storage. citeturn23search1
- Milvus має Milvus Backup як CLI/API інструмент для backup/restore. citeturn23search2turn23search14

Якщо ж ваш default — PostgreSQL, резервне копіювання/відновлення — стандартний layer (logical backups `pg_dump`, physical/WAL залежно від RPO/RTO), але це вже “звичайний Postgres ops”.

### Оцінка витрат (модель, яку можна підставляти числа)

Вартість hosted MCP “memory+tasks” зазвичай складається з 4 компонентів:

1) **Compute gateway** (CPU, мережа, SSE connections)
2) **DB storage + indexes** (вектори + метадані + task tree + audit)
3) **Embeddings** (якщо ви хостите їх або оплачуєте external API)
4) **Observability + backups**

Найбільш “пряма” змінна — embeddings. Якщо ви робите external embeddings через OpenAI `text-embedding-3-small`, ціна $0.02/1M tokens (batch дешевше). citeturn30view2 Це дозволяє рахувати: `tokens_ingested_per_month / 1M * $0.02`.

Для інфраструктурного орієнтиру по розгортанню MCP серверів у production, AWS має публічний приклад “guidance for deploying MCP servers on AWS”, де в репозиторії згадується орієнтовна місячна вартість для помірного трафіку (~$194/міс у прикладі). Це не ваш exact cost, але корисний sanity-check для “base infra”. citeturn33search12

**Практичний спосіб дати cost estimation для 1K/10K/100K users** (без самодурних “точних цифр”) — фіксувати припущення:
- активні користувачі (MAU),  
- requests/user/day,  
- % write operations (embedding потрібен),  
- середній chunk size (tokens),  
- середній обсяг векторів на user (кількість items),  
і показати 3 сценарії (low/median/high). Це краще, ніж псевдо‑точні долари без чітких припущень.

## Legal, compliance, and risk assessment

### Open-source ліцензії та dual-license: що реально можливо

MIT ліцензія прямо дозволяє commercial use (з умовою збереження copyright/license notice). Якщо ваші існуючі open-source MCP сервери під MIT, ви не зможете “заборонити” комерційне використання цієї ж версії коду — будь‑хто може вибрати MIT‑гілку. Тому “dual license MIT + commercial” часто практично не дає важеля — монетизація має йти через hosted сервіс, enterprise features або новий продукт. citeturn8search2turn8search0

Apache 2.0 також permissive і дозволяє комерційне використання (з умовами щодо notice/ліцензійного тексту та інших вимог ліцензії). citeturn8search1turn8search12

Якщо ви хочете dual‑licensing (наприклад, community edition + commercial enterprise), ключова умова — **консолідовані права на внески**: або ви володієте copyright, або маєте CLA/угоди з контриб’юторами, інакше потрібно отримувати дозвіл кожного контриб’ютора для relicensing. citeturn8search3turn8search18

### GDPR: чому “developer knowledge/tasks” майже завжди стає персональними даними

GDPR визначає personal data як будь‑яку інформацію, що стосується ідентифікованої або такої, що може бути ідентифікована, фізичної особи. У developer knowledge/tasks майже завжди є: імена, user IDs, онлайн‑ідентифікатори, контекст комунікацій, інциденти тощо — тобто GDPR застосовний. citeturn9search0turn9search16

Для hosted продукту ви майже напевно будете “processor” (обробник) відносно клієнта‑компанії (controller), але це залежить від того, чи ви визначаєте “цілі та засоби обробки”. Єврокомісія чітко пояснює різницю controller/processor на практичному рівні. citeturn9search10

Щодо data residency: GDPR сам по собі не завжди вимагає “зберігати дані тільки в ЄС”, але жорстко регулює **передачу даних за межі ЄС** через механізми adequacy/запобіжники. Єврокомісія описує ці правила для бізнесів. citeturn9search7  
В enterprise‑угодах вимога “EU-only” часто з’являється як контрактний/регуляторний ризик‑контроль — тому у вас має бути SKU “EU region”/“dedicated deployment”.

### Security ризики, специфічні для MCP hosted сервера

1) **Token passthrough / confused deputy**: специфікація прямо забороняє прокидати токен клієнта далі, вимагає audience validation і коректний `resource` parameter; це критично, якщо ваш сервер буде “проксі” до інших API або буде виконувати інтеграційні дії. citeturn19view0  
2) **Session hijacking / event injection**: guidance говорить не використовувати session як auth та валідувати inbound requests. citeturn19view1  
3) **Еволюція протоколу**: Tasks — experimental, SDK tiers ще формалізуються (публікація tier assignments запланована на 23 лютого 2026). Це створює ризик “spec drift” і потребує контрактних інтеграційних тестів із клієнтами. citeturn18view0turn36view0

### Risk register (узагальнений)

Найбільш “вантажні” ризики для вашого задуму:
- **Protocol risk** (швидкі зміни MCP, experimental Tasks) → ізоляція transport‑шару, compatibility tests, versioned endpoints.
- **Security risk** (OAuth correctness, token misuse, multi-tenant isolation) → мінімізація довіри, аудит логів, RLS/tenant isolation, security review проти MCP guidance.
- **Unit economics risk** (power users/високий write‑трафік embeddings) → BYOK, metered billing, чіткі limits і overages.
- **Competition risk** (MCP hosting платформи) → диференціація як “agent state + workflow”, а не “hosting”.
- **Compliance sales friction** → enterprise features (SSO/audit/data residency/dedicated), DPA процес.

## 90-day launch roadmap

Нижче — “агресивний, але реалістичний” 90‑денний план для private beta. Він спеціально йде від *transport+auth+multi-tenancy* (must-have) до *фіч* (memory/tasks) і лише потім до “полірування”.

**Перший місяць**
- Зафіксувати “contract” продукту: які MCP tools/resources/prompts ви експонуєте; як саме об’єднуються Memory і Tasks в один namespace.
- Реалізувати Streamable HTTP endpoint (GET+POST) + SSE streaming + heartbeat + backpressure.
- Реалізувати API-key auth як Bearer token + tenant resolution + rate limiting.
- Замінити SQLite на production datastore: Postgres + pgvector як базовий backend, з міграцією схем під memory items і task tree.
- Мінімальний “observability baseline”: request logs, latency percentiles, error capture (щоб відразу бачити production edges).

**Другий місяць**
- Зібрати “semantic memory core”: ingest → normalize tags → embed → store → hybrid retrieval (vector + metadata filters).
- Зібрати “task core”: tree operations, status workflows, time tracking, vector search по задачах.
- Додати background jobs (worker) для batch ingest/re-embed, TTL cleanup, exports.
- Впровадити першу версію Admin Panel у Brain (Laravel): tenants, API keys, quotas, usage dashboard, manual billing flags.
- Пілотна інтеграція “BYOK embeddings” + опція “managed embeddings” (може бути тільки для Pro/Business).

**Третій місяць**
- Spec‑aligned OAuth 2.1 (мінімальний піднабір, сумісний з MCP authorization discovery) як beta feature; паралельно з API keys.
- “Hardening sprint”: load tests на SSE, DB contention, worst-case bulk operations; визначити SLO/SLA.
- Backup/restore story (Postgres стандарт + опції, якщо будете підтримувати Qdrant/Weaviate як backend).
- Публічний launch пак: доки, quickstarts (Docker + Cloud), security whitepaper (короткий), pricing v1.
- Private beta з 5–15 командами, які вже юзають MCP‑клієнти; збір метрик: retention, requests per tenant, % writes, середній latency, conversion triggers.

Як критерії “готовності до комерційного запуску” варто формалізувати: (а) стабільність Streamable HTTP + SSE, (б) відсутність tenant data leaks (RLS/policies/тести), (в) прозора metering/billing модель, (г) контроль embeddings cost через BYOK або лиміти, (д) зрозумілий self-hosted Docker шлях із ліцензією.