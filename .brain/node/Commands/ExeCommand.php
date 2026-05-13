<?php

declare(strict_types=1);

namespace BrainNode\Commands;

use BrainCore\Archetypes\CommandArchetype;
use BrainCore\Attributes\Meta;
use BrainCore\Attributes\Purpose;
use BrainCore\Compilation\Store;

#[Meta('id', 'exe')]
#[Meta('description', '<description here>')]
#[Purpose('Command for execute task from Jira')]
class ExeCommand extends CommandArchetype
{
    /**
     * Handle the architecture logic.
     */
    protected function handle(): void
    {
        $this->guideline('input')
            ->text(Store::as('TASK_SOURCE', '$ARGUMENTS'))
            ->text('Аргумент має два типи: (1) ціле число (наприклад `123`, `42`) — це ID векторної задачі з vector-task; (2) код з літер, можливо змішаний з цифрами (наприклад `FEAT-1`, `REFACT-5`, `OLOM-440-on-review`) — це назва папки в `.docs/tasks/`.')
            ->text('ПЕРЕД будь-якими діями детектуй тип `$TASK_SOURCE`: якщо весь рядок складається тільки з цифр (`ctype_digit`) → джерело векторна задача (VECTOR-SOURCE); інакше → джерело папка з задачею (FOLDER-SOURCE). Подальші guidelines і rules діляться на дві гілки залежно від детекції.');

        $this->guideline('folder-with-tasks')
            ->text('[FOLDER-SOURCE] Цей блок застосовується ТІЛЬКИ якщо `$TASK_SOURCE` — код з літер (наприклад `FEAT-1`, `REFACT-5`). Тоді задачі зберігаються в папці `.docs/tasks/`. Кожна задача — окрема папка з `task.md` та, можливо, додатковими файлами (`video.mp4`, `img.png` тощо).');

        $this->guideline('task-structure')
            ->text('[FOLDER-SOURCE] Структура папкової задачі: `.docs/tasks/{$TASK_SOURCE}/task.md` містить опис задачі, вимоги та інструкції. Інші файли в папці — допоміжні матеріали.')
            ->text('[FOLDER-SOURCE] Папка задачі ({$TASK_SOURCE}) може мати постфікс `-done` або `-on-review` — задача вже виконана або на рев\'ю відповідно. Якщо постфікс `-on-review`, теоретично можемо повернутись до задачі й дороблювати зауваження тімліда.');

        $this->guideline('vector-task-source')
            ->text('[VECTOR-SOURCE] Цей блок застосовується ТІЛЬКИ якщо `$TASK_SOURCE` — ціле число (наприклад `123`). Тоді задача береться з vector-task через MCP, а НЕ з папки `.docs/tasks/`.')
            ->text('[VECTOR-SOURCE] Виклич `mcp__vector-task__task_get({"task_id": "$TASK_SOURCE"})` щоб отримати повний опис: `title`, `description`, `tags`, `status`, `priority`, `parent_id`, children. Згідно iron rule `explore-before-execute` обов\'язково підтягни parent (через `task_get` по `parent_id`) і children (через `task_list` з фільтром `parent_id`) — це контекст і залежності.')
            ->text('[VECTOR-SOURCE] У векторної задачі НЕМАЄ файлу `task.md` і допоміжних файлів — весь зміст у полях задачі. Якщо в `description` є посилання на репо-файли (`.docs/...`, `app/...`) — прочитай їх для контексту.')
            ->text('[VECTOR-SOURCE] Лайфцикл статусу описаний правилом `after-user-plan-apruve` нижче: НЕ створюй нову задачу у vector-task, лише оновлюй статус існуючої через `task_update`.');

        $this->guideline('what-needs-to-be-executed')
            ->text('[FOLDER-SOURCE] Вивчи матеріали в `.docs/tasks/{$TASK_SOURCE}`, особливо `task.md`. Зверни увагу на вимоги та інструкції.')
            ->text('[VECTOR-SOURCE] Вивчи `title` + `description` векторної задачі, parent context, children (subtasks). Якщо `description` посилається на код або доки — прочитай ці файли.')
            ->text('У будь-якому випадку: вникни повністю в задачу, вивчи всі матеріали, тести, документацію в `.docs` й кодову базу максимально детально.')
            ->text('Після аналізу, якщо будуть питання або потрібні уточнення — питай. Я тут щоб допомогти зрозуміти задачу і виконати її якнайкраще.');

        $this->guideline('execute-task')
            ->text('Після того, як ти повністю зрозумієш задачу і всі її вимоги, приступай до виконання з урахуванням правила "pre-code-approval-gate". Виконуй задачу відповідно до інструкцій в `task.md` і використовуй кодову базу та інші матеріали для допомоги у виконанні. Якщо під час виконання виникнуть питання або потрібна допомога, не вагайся звертатися до мене за підтримкою.');

        $this->guideline('after-complete-and-before-commit')
            ->text('Перед звітом про готовність задачі обовʼязковий порядок: (a) пройти `code-review-self-checklist` (12 пунктів конвенцій тімліда); (b) самостійно прогнати тести/PHPStan/Rector/Pint; (c) тільки тоді звітувати користувачу зі списком команд для верифікації.')
            ->text('Команди для верифікації мною: тести через `./vendor/bin/sail test {file,file,file...}`, PHPStan через `./vendor/bin/sail composer test:types -- analyse {file,file,file...}`, PHPRector через `./vendor/bin/sail composer test:refactor -- {file,file,file...}`, Pint через `./vendor/bin/sail composer test:lint -- {file,file,file...}`. Спочатку САМ перевір і виправ — потім давай мені.')
            ->text('Якщо все добре — даю апрув на комміт. Якщо є проблеми — вказую і прошу виправити.')
            ->text('Згенеруй мені готові команди скопіювати-вставити для КОЖНОГО зміненого файла окремо, щоб я не складав їх вручну.')
            ->text('Якщо у задачі були торкнуті translations — окремою секцією перерахуй усі нові `__(\'group.key\')` ключі, які клієнт має додати через operator UI Spatie Translation Loader.');

        $synthesized = 'Синтезовані з цих розмов конвенції лежать у `.docs/guides/05-code-review-conventions.md` (controllers, routes, requests, resources, translations)';
        if ($this->var('EXE_GIT_BRANCHING')) {
            $synthesized .= ', `.docs/guides/06-workflow-policy.md` (branching, PR lifetime, refactoring budget, environments)';
        }
        $synthesized .= ' та `.docs/guides/07-performance-patterns.md` (eager loading, async, no new indexes).';

        $this->guideline('team-leader-conversation')
            ->text('У мене є тімлід (Michael), який детально описав свої вимоги до коду і процесу виконання задач. Стенограми розмов з ним: `.docs/conversations/01.md` (workshop performance + code review preferences), `.docs/conversations/02.md` (environments, deploy, async loading, Desk365), `.docs/conversations/about-task-outside.md` (small-fixes-direct-to-main, refactoring branches).')
            ->text($synthesized)
            ->text('Я повинен бути уважним до деталей цих документів і слідувати інструкціям тімліда, щоб мій код проходив його code review з першого разу.');

        $reading = 'Перед тим як починати planning або питання, обов\'язково прочитай у такому порядку: ';
        $reading .= '(1) джерело задачі — для FOLDER-SOURCE це `.docs/tasks/{$TASK_SOURCE}/task.md`, для VECTOR-SOURCE це `mcp__vector-task__task_get({"task_id": "$TASK_SOURCE"})` + parent + children; ';
        $reading .= '(2) `.docs/guides/05-code-review-conventions.md` — як писати код щоб пройти review; ';
        $next = 3;
        if ($this->var('EXE_GIT_BRANCHING')) {
            $reading .= "($next) `.docs/guides/06-workflow-policy.md` — branching та PR policy; ";
            $next++;
        }
        $reading .= "($next) `.docs/guides/07-performance-patterns.md` — якщо задача стосується списків/фільтрів/повільних сторінок.";

        $this->guideline('mandatory-pre-execution-reading')
            ->text($reading)
            ->text('Conversations (`.docs/conversations/*.md`) — читай тільки коли треба зрозуміти контекст конкретної фрази з guides або коли тімлід посилається на минулу розмову. Інакше guides уже містять синтез.');

        $this->guideline('docs-discovery')
            ->text('Окрім обовʼязкового reading-списку вище, для пошуку релевантних `.docs/` файлів використовуй `mcp__brain-tools__docs_search({"keywords": "..."})` — це primary tool для семантичного discovery (повертає paths, matches, scores). Шукай по ключових словах задачі: домен/модуль/feature/технологія.')
            ->text('Викликай ОБОВʼЯЗКОВО коли: (1) задача згадує домен/модуль яких немає в обовʼязковому reading (Events, Market, Rideshare, Credits тощо); (2) треба знайти ADR/architecture/technical-decision документ; (3) потрібен історичний контекст рішення; (4) перед тим як казати "не знайшов інформації в .docs" — спочатку зроби семантичний пошук.')
            ->text('НЕ використовуй `Glob`/`Grep`/`Read` для пошуку у `.docs/` коли можна `docs_search` — він точніший і дешевший.');

        $this->guideline('chrome-testing')
            ->text('В тебе є доступ до Chrome і ти можеш візуальні частини які треба перевірити через браузер, перевіряти сам, я вітповідно буду це бачити, якщо сожеш сам в браузері щось зробити, то роби, я завжди слідкую за тобою і бачу що ти викликаєш і що робиш, тому користуйся браузером по повній.');

        $this->rule('phpstan-important')
            ->critical()
            ->text('Максимально уникай використання "@phpstan-ignore-next-line" в PHPStan без дуже вагомої причини. Якщо ти вважаєш, що це необхідно, спочатку спробуй виправити проблему, яка викликає помилку PHPStan, замість того, щоб ігнорувати її. Якщо ти все ж таки вважаєш, що використання "@phpstan-ignore-next-line" є єдиним виходом, обов\'язково поясни причину цього рішення в коментарі поруч з ним.');

        $this->rule('phpstan-and-phprector-check-areas')
            ->critical()
            ->text('Перевір спочатку зони де перевіряють PHPStan і PHPRector в файлах `phpstan.neon` і `rector.php` щоб не перевіряти ті діректорії які не обслуговуються їми.');

        $this->rule('foundation-docs-blocker')
            ->critical()
            ->text('ЗАБОРОНЕНО ставити користувачу будь-які уточнюючі питання, формувати plan або входити у `pre-code-approval-gate` ПОКИ не прочитані ВСІ foundation-документи проекту у такому порядку: (1) `.docs/original-client-requirements.md` — оригінальні вимоги клієнта (Harald Burgstaller / Silvia Sellemond); (2) `.docs/Pflichtenheft Community-Plattform MVP v1.0.docx.md` — повний Pflichtenheft MVP (єдина authoritative specifikation scope); (3) `.docs/our-estimation.md` — фази, estimation, out-of-scope. Цей блок виконується ПЕРЕД `mandatory-pre-execution-reading` (guides/05,06,07): спочатку бізнес-контекст і scope MVP, потім інженерні конвенції.')
            ->text('Читання має бути ПОВНИМ, а не семантичним пошуком: `Read` цілих файлів, не `docs_search` фрагментів. `docs_search` — для додаткових тем поверх foundation, а не замість нього.')
            ->text('Якщо хоч один з трьох foundation-файлів відсутній на диску — STOP, повідом користувачу про відсутній файл і не починай інтерпретацію задачі без нього.')
            ->why('Festpreis 50 000 EUR + 360h не дає права на цикли «питання → відповідь уже в Pflichtenheft». Без foundation Brain плутає Out-of-Scope з In-Scope, помиляється з фазою (Phase 1/2/3/4), пропускає DSGVO-обмеження і ставить питання, відповіді на які вже зафіксовані в client-requirements. Емпірично: вже минимум 2 рази Brain починав постановку питань, прочитавши лише `our-estimation.md`.')
            ->onViolation('STOP. НЕ став жодного уточнюючого питання користувачу. Прочитай усі 3 foundation-файли підряд через `Read` (не `docs_search`). Тільки після цього формулюй питання — і ТІЛЬКИ ті, чого об\'єктивно немає у foundation. У відповіді користувачу явно перерахуй, які саме foundation-файли прочитав і які scope-обмеження з них застосовуєш до задачі.');

        $this->rule('pre-code-approval-gate')
            ->critical()
            ->text('Before writing or editing ANY PHP file, Brain MUST: (1) describe WHAT will be changed and WHERE (file, class, method), (2) explain WHY the change is needed, (3) outline HOW it will be implemented (approach, patterns, key decisions), (4) ask the user if they have questions or clarifications. Code writing proceeds ONLY after explicit user approval.')
            ->why('Prevents premature or misaligned code changes. Ensures the user understands and agrees with the approach before any file is modified. Reduces rework and maintains shared understanding of architectural decisions.')
            ->onViolation('STOP code generation immediately. Present the plan to the user. Wait for explicit approval before proceeding with Edit/Write.');

        $this->rule('convention-compliance-gate')
            ->critical()
            ->text('У плані виконання задачі (перед `pre-code-approval-gate`) Brain ОБОВʼЯЗКОВО маркує, які конвенції з `.docs/guides/05-code-review-conventions.md` застосовуються: чи новий endpoint → single-action `__invoke` controller; чи routes по ресурсу; чи `request->array()` для масивів; чи `Resource::collection()` через `response()`; чи будуть зачеплені translations; чи зачеплений existing controller (тоді — наскільки він великий, і чи варто розпиляти). Якщо задача про list/filter/slow page — окремо маркує застосування правил з `.docs/guides/07-performance-patterns.md`.')
            ->why('Тімлід ріже PR на code review саме за невідповідність цим конвенціям. Якщо проявити їх у плані, користувач може скоригувати підхід ДО написання коду, а не після review.')
            ->onViolation('STOP. Перепиши план з явним маркуванням релевантних конвенцій. Не починай Edit/Write поки користувач не апрувне.');

        $this->rule('translations-spatie-loader-blocker')
            ->critical()
            ->text('НІКОЛИ не редагуй `lang/*.php`, `resources/lang/*`, `LanguageLineSeeder.php` або інші мовні файли при додаванні нових UI-стрингів. OLC використовує `spatie/laravel-translation-loader` — переклади живуть у БД-таблиці `language_lines` і додаються клієнтом через operator UI. У коді залишай ТІЛЬКИ виклик `__(\'group.key\')`. Після виконання задачі перерахуй користувачу всі нові ключі, які клієнт має додати через UI.')
            ->why('Прямі правки lang-файлів = автоматичне відхилення PR на code review. Це зафіксовано і в guides/05, і в memory feedback `feedback_olc_translations_no_seeder.md`.')
            ->onViolation('Видали всі правки в lang-файлах і LanguageLineSeeder. Залиш у коді тільки `__()` виклики. У звіті користувачу окремою секцією — список ключів для operator UI.');

        $this->rule('performance-task-trigger')
            ->high()
            ->text('Якщо `task.md` згадує "повільно", "slow", "long load", "N+1", фільтри/списки на великих таблицях, або задача з префіксом REFACT/performance — ОБОВʼЯЗКОВО прочитай `.docs/guides/07-performance-patterns.md` перед planning. У плані маркуй: (1) чи плануєш профіль на `beta.olc.omas.com` (debug toolbar); (2) чи будеш видаляти wasted eager loading; (3) чи треба ділитися pre-loaded колекціями між викликами; (4) чи планується async через job/Livewire; (5) ЗАБОРОНЕНО додавати нові індекси на хот-таблиці без явного дозволу тімліда (через bigint-міграцію в кінці року).')
            ->why('Performance-задачі мають специфічний playbook у тімліда: cache — last resort, indexes — заблоковані, beta — основний інструмент діагностики. Без читання guides/07 рішення майже завжди буде відхилене.')
            ->onViolation('STOP. Прочитай `.docs/guides/07-performance-patterns.md`, перепиши план з маркерами вище. Якщо здається, що індекс необхідний — пиши користувачу окремим питанням з обґрунтуванням.');

        $this->rule('git')
            ->critical()
            ->text('Після виконання задачі згенеруй commit message (без води, тільки по справі що було зроблено) — я його маю заапрувити. БЕЗ `Co-Authored-By: Claude` trailer, бо комміт має бути від мого імені. Після апруву роби `git commit`.');

        if ($this->var('EXE_GIT_BRANCHING')) {
            $this->rule('git')
                ->text('Перед виконанням: перейти на `master`, зробити `git pull`, потім створити (якщо ще нема) гілку повністю в нижньому регістрі.')
                ->text('[FOLDER-SOURCE] Branch: `feature/task-{NORMALIZED_TASK_SOURCE}`, де NORMALIZED_TASK_SOURCE — це `$TASK_SOURCE` з відрізаними status-суфіксами `-on-review`, `-done`, `-next`, `-on-hold`, `-in-progress`. Приклад: `OLOM-440-on-review` → `feature/task-olom-440`.')
                ->text('[VECTOR-SOURCE] Branch: `feature/task-vt-{$TASK_SOURCE}` (наприклад id `123` → `feature/task-vt-123`). Якщо у векторної задачі є коротка змістовна назва або slug — додай через дефіс: `feature/task-vt-123-fix-credit-ledger`.')
                ->text('Після коміту `git push` і Merge request я роблю руками.')
                ->text('Якщо задача насправді не feature а рефакторинг ([FOLDER-SOURCE] з префіксом REFACT-* або task.md/vector task явно про рефакторинг) — гілку називай `refactoring/<scope>` замість `feature/task-...`. Дрібні фікси поза задачею в `/exe` не пушити — це робиться окремо прямо в `master` без гілки.');

            $this->rule('pr-lifetime-warning')
                ->high()
                ->text('Тімлід вимагає закривати PR протягом максимум 2 тижнів. Перед `git push` нагадай користувачу про це обмеження одним рядком, щоб він планував merge час.')
                ->why('Stale PRs накопичують конфлікти і втрачають контекст. Це зафіксовано в `.docs/guides/06-workflow-policy.md`.')
                ->onViolation('Додай рядок-нагадування у фінальному звіті користувачу: "PR має бути зведений протягом 2 тижнів — інакше треба буде або сплітити, або закривати."');
        }

        $this->rule('code-review-self-checklist')
            ->critical()
            ->text('ПЕРЕД тим як казати користувачу "задача готова, перевір" і генерувати commit message, Brain ОБОВʼЯЗКОВО проганяє по своєму diff цей чек-лист (відповідає `.docs/guides/05-code-review-conventions.md`):')
            ->text('(1) Контролер не виріс понад ~300 рядків? Якщо я додавав логіку до існуючого 700+ контролера — створив дедикований замість цього?')
            ->text('(2) Новий endpoint — це single-action `__invoke` controller, а не новий метод у multi-action контролері?')
            ->text('(3) Route URI названий по ресурсу (`customers/blocked-addresses`), а не по фічі (`barcode/blocked-addresses`)?')
            ->text('(4) Параметри-масиви беруться через `$request->array(\'key\')` без зайвого FormRequest typing?')
            ->text('(5) FormRequest без `authorize()` стуба, якщо authorization не потрібна?')
            ->text('(6) `Resource::collection(...)` повертається через `response(...)` для коректного `JsonResponse` типу?')
            ->text('(7) Жодних правок у `lang/*.php` / `resources/lang/*` / `LanguageLineSeeder` — тільки `__()` у коді?')
            ->text('(8) JS — Axios, не `$.ajax`. Без inline `style="..."`. User-controlled значення проганяються через `escapeHtml()` / `.text()` перед інʼєкцією в HTML?')
            ->text('(9) Pest тести написані для нової feature?')
            ->text('(10) Порожній рядок після `->get()` перед наступним Eloquent ланцюжком?')
            ->text('(11) Імена функцій — конкретні (`isBlocked()`), не абстрактні?')
            ->text('(12) Немає двох сусідніх `<div>` що рендерять один концептуальний блок?')
            ->text('Якщо ХОЧ ОДИН пункт failed — зупинись, пофікси, потім звітуй.')
            ->why('Це дзеркало того, що тімлід ріже на code review. Самоперевірка перед звітом економить йому і мені цикл review-fix.')
            ->onViolation('STOP. Не кажи що готово. Пройдись по списку, виправ що відхилилось, тоді звітуй.');

        $this->rule('code-quality-and-testing-user-gates')
            ->critical()
            ->text('Після виконання задачі, перед коммітом, я повинен вручну перевірити код за допомогою тестів, PHPStan, PHPRector і Pint. Якщо є якісь проблеми з кодом або він не відповідає вимогам задачі, я вкажу на це і попрошу виправити перед коммітом. Якість коду і відповідність вимогам є дуже важливими, тому я завжди готовий допомогти досягти найкращого результату.');

        $this->rule('communication-and-support')
            ->high()
            ->text('Під час виконання задачі, якщо виникнуть будь-які питання або потрібна допомога, я не повинен соромитися звертатися до мене за підтримкою. Я тут, щоб допомогти зрозуміти задачу і забезпечити успішне її виконання. Відкрита комунікація є ключем до успіху в цьому процесі.');

        $this->rule('before-execution-gate')
            ->critical()
            ->text('Перед виконанням треба відтворити проблему, кажеш мені що зробити щоб я бачищо що треба зробити, як треба зробити і як має бути, якщо треба дії в браузері (локальний урл http://localhost:8087/) кажеш куди натиснути й що має відкритися, якщо треба виконати якусь команду в терміналі кажеш яку команду і що має відбутися після її виконання. Я маю повністю зрозуміти задачу і її вимоги, перш ніж починати кодити. Я повинен бути дуже уважным до деталей і слідувати твоим інструкциям, чтобы обеспечить качество и соответствие кода твоим ожиданиям.');

        $this->rule('after-execution-gate')
            ->critical()
            ->text('Після виконання задачі, ти кажеш куди зайти що нажати та що перевірити щоб я самостійно візуально переконався що задача виконана');

        $this->rule('answer-and-instructions-for-user')
            ->critical()
            ->text('Давай мені інструкції не всі одразу а покроково, по одному маленькому кроку, щоб я міг виконувати їх по черзі і не заплутатися і звітувати тобі що я бачу. Якщо інструкція має кілька кроків, розбий її на окремі повідомлення, щоб я міг виконувати їх по черзі і не заплутатися. Я буду звітувати тобі що я бачу після кожного кроку, щоб ти міг переконатися що я рухаюсь в правильному напрямку і розумію задачу правильно.');

        $this->rule('delegation-non-trivial-only')
            ->critical()
            ->text('Brain delegates research, exploration, analysis, and validation tasks to specialized agents. EXCEPTION: code generation, editing, and writing MUST be performed by Brain directly — never delegated to agents.')
            ->why('Brain has full conversation context and direct file access for consistent code generation. Agents excel at research and analysis but produce inconsistent code without full context.')
            ->onViolation('For code tasks: use Edit/Write directly. For research/analysis: delegate to appropriate agent via Task() tool.');

        $this->rule('after-user-plan-apruve')
            ->critical()
            ->text('Після того як я затверджу план виконання, керуй статусом задачі у vector-task залежно від джерела:')
            ->text('[FOLDER-SOURCE] Створи відповідний запис у vector-task через `mcp__vector-task__task_create` (title із `task.md`, опис стислий, тег з префікса коду). Перед виконанням постав `in_progress`, після коміту — `completed`.')
            ->text('[VECTOR-SOURCE] НЕ створюй нову задачу — вона вже існує. Просто оновлюй статус існуючої через `mcp__vector-task__task_update({"task_id": "$TASK_SOURCE", "status": "in_progress"})` перед стартом і `"completed"` після коміту. Згідно iron rule `parent-readonly` — НЕ оновлюй parent.');

        $this->rule('conversetion-with-user')
            ->critical()
            ->text('Не пиши мені цілі простині повідомлень, видавай мені інформацію і питання порційно а не все разом. Не треба і питанні і план разом змішувати, абсолютно все послідовно, крок за кроком, маленькими кроками.');
    }
}
