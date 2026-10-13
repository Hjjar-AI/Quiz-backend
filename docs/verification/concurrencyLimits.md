# Backend concurrency limits

Verified 2026-10-10 on Python 3.14.4, Django 6.1.2 and PostgreSQL 18.6; baseline `8274707` plus the current workspace changes. [Test source](../../tests/edge_cases/test_concurrency_limits.py) · [Structured measurements](concurrencyDetails.json) · [Full suite](pythonTests.md).

**35 new scenarios passed in three consecutive PostgreSQL runs**, with 38 synchronized bursts per run and up to **16 simultaneous database workers**. The earlier two-thread master-finish test also remains covered by the full suite. This verifies the listed transaction behavior; maximum HTTP throughput or simultaneous user capacity has not been established.

The final full PostgreSQL suite passed **971/971 tests in 104.435 seconds**. SQLite passed **935 tests with 36 intentional locking skips** out of 971 in 35.038 seconds. No unexpected failures, errors or deadlocks occurred in these passing runs.

## What this means for the number of users

**Directly tested: 16 distinct users submitting learning completions simultaneously against one shared question.** All 16 writes succeeded and preserved the totals in each focused run; the entire burst took approximately **1.38–1.95 seconds**. Other 16-worker scenarios repeat requests for a single user. These demonstrate transaction correctness under a small burst, rather than a 16-user maximum or a deployed response-time guarantee.

**Approximate active-user capacity depends on how frequently each user sends requests and how long those requests occupy a server worker.** A signed-in user reading a question between requests occupies no HTTP worker. Registered accounts, signed-in users, users actively sending requests and requests being processed simultaneously are different counts.

For the source launcher's **3 sync workers**, the following is an illustrative sizing model using **50% average worker utilization** to leave headroom:

```text
request budget per second = 3 workers × 0.5 ÷ average worker time per request
active users ≈ request budget per second × seconds between requests per user
```

| Assumed average worker time per request | Modeled request budget | Active users: 1 request every 10 seconds | Active users: 1 request every 30 seconds |
| ---: | ---: | ---: | ---: |
| 0.10 seconds | 15/second | ~150 | ~450 |
| 0.25 seconds | 6/second | ~60 | ~180 |
| 0.50 seconds | 3/second | ~30 | ~90 |
| 1.00 second | 1.5/second | ~15 | ~45 |

**Example: around 90 active learners is the modeled load if the average request occupies a worker for 0.5 seconds and each learner sends one backend request every 30 seconds.** At one request every 10 seconds, the same assumptions give around 30 active learners. These numbers are conditional estimates, not measured supported-user counts. The request times and cadences in this table are assumptions; the chosen 50% utilization is illustrative and does not guarantee acceptable latency.

Include **all** requests in the cadence: fetching questions, saving answers, polling, clock/status updates and other background calls. An action producing three requests consumes three times the request budget. Expensive exports/imports, shared-row contention, real authentication/cache costs and other processes can reduce capacity. The table assumes steady, spread-out traffic and roughly unchanged request cost under that load.

Synchronized starts or finishes create queues even with fewer users. For example, **90 simultaneous requests** with 3 available workers and a constant 0.5-second request time would take about **15 seconds** to drain, ignoring network overhead and additional contention. The existing 16-thread service tests bypass this 3-worker HTTP queue. PostgreSQL's 97 ordinary connection slots do not translate directly into 97 learners.

To replace these estimates with a supported user count, measure the actual deployment's request mix and cadence, then increase simulated distinct users while checking latency targets, errors and database/cache contention. The existing test evidence supports the 16-user transaction burst; the table explains how larger active populations could fit when their requests are spaced out.

## Installed and configured limits

| Limit | Current value | Meaning |
| --- | --- | --- |
| PostgreSQL `max_connections` | 100 | Shared by the whole cluster, including other databases and clients. |
| Superuser / additional reserved connections | 3 / 0 | At most 97 ordinary connections before accounting for other clients; not 97 users. |
| `mpsql` role connection limit | -1 | No separate role cap; cluster capacity still applies. |
| Transaction isolation | Read committed | Tested guards depend on explicit locks, revisions and constraints. |
| Database `lock_timeout` / `statement_timeout` | 0 / 0 | Neither timeout is enabled on the inspected connection. The tests' timeouts below do not change application settings. |
| Database `deadlock_timeout` | 1 second | Delay before checking for a deadlock, not a transaction duration limit. |
| Production launcher | 3 Gunicorn workers | `scripts/quiz_start.sh` supplies no worker-class/thread override; absent external overrides, sync workers handle one request each. This launcher was not started or benchmarked. |
| Master exam size | 200 questions | Current source setting; competing appends tested with a temporary cap of 2. |
| Selected offline allowance | 200 distinct questions per user | Current source fallback; competing pack requests tested with a temporary cap of 2. Full-bank policy is separate. |

Database settings were read through `test_quiz_codex_20261010`. No server/role settings, application data, migrations, dependencies or launcher configuration were changed.

## Verified scenarios

Worker counts describe simultaneous actions within each test. Rejections below are expected outcomes and are asserted alongside committed database state.

| Area (number of tests) | Workers | Verified result |
| --- | --- | --- |
| Master start / identical answers / different answers / finish / answer versus finish (5) | 4 / 4 / 2 / 16 / 2 | Start reuses one attempt; identical answers preserve one timestamp; competing different answers yield one winner and one `ATTEMPT_PROGRESS_CHANGED`; finish credits learning once. Answer/finish ordering produces consistent saved answers and learning, with `ATTEMPT_ALREADY_COMPLETE` permitted for the late answer. |
| Ordinary start / answer / finish (3) | 4 / 2 / 4 | Start replaces prior sessions and leaves one active session; competing answer baselines conflict. Finish service has one success and three `ValueError` rejections, with one history/event/learning credit. These are service semantics, not an HTTP receipt guarantee. |
| Question / planner / group / master composition revisions (4) | 2 each | One winner, one stale-write rejection. Planner revision advances monotonically; signals can advance it more than once. |
| Question receipt replay / changed body / category receipt replay (3) | 4 / 2 / 4 | Identical creation identity creates one target; changed question body with the same identity yields 201/409. Category replay creates one category. |
| Explicit bookmark / legacy toggle / question flag (3) | 16 / 2 / 4 | Explicit desired state leaves one bookmark; two legacy toggles reverse each other; repeated flags create one open flag. |
| Learning duplicate source / distinct sources / shared question / presentation (4) | 16 / 2–16 / 16 / 4 | Duplicate source credits once; distinct events preserve all event, user, question, learning-day and planner counts; 16 users preserve shared question totals; repeated presentation credits once. |
| Offline allowance / completion replay / changed completion (3) | 4 / 4 / 2 | Two pack successes and two 403s at quota 2; identical completion creates one receipt/history/learning credit; changed completion body yields 200/409. |
| Runtime-settings / tag-tree revisions (2) | 2 each | One 200 and one 409 from the same baseline. |
| Reciprocal tag parenting / group membership / master question cap (3) | 2 / 4 / 4 | One parent change succeeds and the cycle-producing change rejects; one membership pair; one append succeeds from size 1 at cap 2, three reject. |
| Duplicate state imports (1) | 2 | One UUID remains and local revision advances using `use_imported`. MIME detection is mocked; parsing, transaction locks and database writes are real. |
| Assessed parent edit versus learning completion (1) | 2 | Immutable historical event remains; current question stats and SRS for the old fingerprint are invalidated regardless of ordering. |
| Cross-deactivation of the last two admins (1) | 2 | One 200, one 400; one active admin remains. |
| Lock timeout and recovery (1) | 2 plus lock holder | A held user lock causes SQLSTATE `55P03` at a test-only 200 ms timeout with no partial bookmark. Another user writes successfully; the blocked user succeeds after release. |
| Approximate throttle race (1) | 2 | With a controlled competing-cache-read window, both calls pass a `1/min` throttle; a subsequent call rejects. This is a demonstrated algorithm limit, not a strict concurrency cap. |

Identical master finish, explicit bookmark and receipt-backed completion are safe for the tested duplicates. Ordinary start and legacy toggles have different behavior. Client recovery must follow [write contracts](../contracts/writeRecovery.md) rather than blindly replay every write.

## Measured contention

The first passing run measured distinct learning completions for the **same user and question**, using separate sources. Each burst starts together; later bursts reuse the same fixture. All 30 events and associated counters committed correctly.

| Workers | Burst wall time (s) | Operation p50 (s) | Slowest operation (s) |
| ---: | ---: | ---: | ---: |
| 2 | 0.2030 | 0.1775 | 0.1775 |
| 4 | 0.3303 | 0.1996 | 0.2910 |
| 8 | 0.6711 | 0.3486 | 0.5976 |
| 16 | 1.4565 | 0.6952 | 1.3193 |

Wall time includes thread/connection setup; operation time begins after the barrier and includes lock waiting. p50 is the upper middle observation for these even-sized samples. These small local bursts show increasing contention, not sustained throughput or production latency targets. Run durations were 21.324, 18.674 and 20.471 seconds; timings vary with machine load. All per-burst measurements are retained in the JSON report.

Learning writes for one user serialize behind that user's row; different users can still contend on a shared question. State imports take broad user/question locks. Larger imports and mixed endpoint traffic therefore need separate deployed measurements before sizing workers or changing database limits.

## Rate policy versus concurrency

Current source rates are requests per time window, not simultaneous request caps:

| Scope | Rate |
| --- | --- |
| Anonymous / authenticated default | 100/hour / 1000/hour |
| Login credentials / login IP | 5/min / 30/min |
| CSRF / import / backup / clear database | 30/hour / 10/hour / 5/hour / 2/hour |
| Admin password / bulk verify / PDF export | 50/hour / 30/min / 20/hour |
| Master answer / master start | 2000/hour / 10/hour |

The unused `login` placeholder is 5/min. Scoped throttles derive from DRF `SimpleRateThrottle`. The controlled race demonstrates its non-atomic cache read/write window. Process-local test cache does not verify deployed Memcached/Redis behavior, cross-process limits or a strict login-abuse ceiling. No throttle rewrite was made.

## Reproduce and scope

From `backend/`, with the existing Quiz Python environment and dedicated test database:

```bash
QUIZ_TEST_POSTGRES_DB=test_quiz_codex_20261010 python manage.py test tests.edge_cases.test_concurrency_limits tests.edge_cases.test_concurrency --settings=tests.postgresql_settings --keepdb --noinput
QUIZ_TEST_POSTGRES_DB=test_quiz_codex_20261010 python manage.py test tests --settings=tests.postgresql_settings --keepdb --noinput
python manage.py test tests --settings=tests.test_settings --noinput
```

Run PostgreSQL commands sequentially: they share and flush the same dedicated test database. Never select an application database. Each new race emits a sanitized `CONCURRENCY_RESULT` JSON record. Other suite output can contain generated fixture credentials; retain raw logs privately.

The harness uses independent thread-local connections, a 15-second start barrier, a 30-second worker deadline and per-worker 5-second lock/10-second statement timeouts. The dedicated lock-timeout case uses 200 ms. Test connections close afterward. API scenarios use Django's in-process client with forced authentication; cache, hashing and file storage are isolated test substitutes. SQLite intentionally skips all 35 new PostgreSQL scenarios plus the existing row-locking test.

Not established: saturation at 97/100 connections, maximum users, sustained HTTP throughput, all possible interleavings, multiple deployed processes, real cache/network/authentication cost, large imports, long-running/PDF workloads, operator backup/restore races, native/browser recovery or MariaDB behavior. No connection exhaustion or application-database load test was performed. The verified ceiling is **16 concurrent test workers for these scenarios**, not a newly configured limit.
