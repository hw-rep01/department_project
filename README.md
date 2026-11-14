# منصة القسم الذكية — Smart Department Platform (SDP)

نظام إدارة أكاديمية متكامل لقسم جامعي، يعمل بالذكاء الاصطناعي. مبني بـ **FastAPI** (الخلفية) و**Next.js** (الواجهة)، ويغطي:

- 🤖 **مساعد أكاديمي (RAG):** أسئلة وأجوبة وتلخيص مقيّدين حصراً بملازم المادة، مع استشهاد بالمقاطع `[C1]`.
- 📝 **كويزات ذكية:** توليد كويزات MCQ/صح وخطأ من الملزمة، رصد الأخطاء الشائعة، وجلسة طالب محمية برمز الجلسة.
- 📡 **رادار الفجوات:** تجميع أسئلة الطلاب وأخطاء الكويزات دلالياً (Vector Clustering) لكشف المواضيع غير المفهومة وإطلاق تنبيهات للمدرس ورئيس القسم.
- 🗂️ **تصنيف ومعالجة الطلبات (Triage):** تصنيف آلي (أكاديمي/إداري)، إزالة تكرارات دلالية، دمج الطلبات المتشابهة في دفعات، ومسار تدفق بخمس مراحل حتى القرار النهائي.
- 📅 **جدول دراسي ذكي:** تعديل القاعات والأوقات، كشف التعارضات، اقتراح مواعيد التعويض تلقائياً، وبث حي للتغييرات عبر SSE.
- 📢 **البلاغات والإشعارات:** بلاغات scoped (قسم/مادة/شعبة) مع سجل قراءات، ملخص صباحي، وتذكير قبل المحاضرة.

**الأدوار الخمسة:** طالب · ممثل شعبة · مدرس · مقرر قسم · رئيس قسم — بصلاحيات دقيقة لكل دور (`backend/app/core/permissions.py`).

---

## جدول المحتويات

- [المكدس التقني](#المكدس-التقني)
- [بنية المشروع](#بنية-المشروع)
- [كيف يعمل النظام؟](#كيف-يعمل-النظام)
- [تشغيل المشروع](#تشغيل-المشروع)
  - [التشغيل الكامل عبر Docker (موصى به)](#1-التشغيل-الكامل-عبر-docker-موصى-به)
  - [التشغيل المحلي للتطوير](#2-التشغيل-المحلي-للتطوير)
- [الحسابات التجريبية](#الحسابات-التجريبية)
- [متغيرات البيئة](#متغيرات-البيئة)
- [معالم الـ API](#معالم-الـ-api)
- [المهام المجدولة (Celery Beat)](#المهام-المجدولة-celery-beat)
- [الاختبارات](#الاختبارات)
- [ملاحظات تشغيلية](#ملاحظات-تشغيلية)

---

## المكدس التقني

| الطبقة | التقنية |
|---|---|
| الخلفية | Python 3.11+ · FastAPI · SQLAlchemy 2 · Pydantic v2 |
| قاعدة البيانات | PostgreSQL 16 + امتداد **pgvector** (أو SQLite للتطوير) |
| الطوابير والمهام | Redis · Celery (worker + beat) |
| الذكاء الاصطناعي | LangChain · OpenAI (LLM + التضمين) أو نموذج محلي عبر `sentence-transformers`، مع مزود `stub` للاختبارات |
| المستندات | pypdf لتحميل PDFs · تقطيع (chunking) قابل للضبط |
| الواجهة | Next.js 16 · React 19 · TypeScript · Tailwind CSS (RTL، عربي) |
| النشر | Docker Compose · Nginx كوسيط (يوجّه `/api/` للخلفية و`/` للواجهة) |
| الاختبارات | pytest (72 اختبار خلفية) · Playwright (12 اختبار متصفح E2E) |

---

## بنية المشروع

```text
.
├── backend/                  # خدمة FastAPI
│   ├── app/
│   │   ├── main.py           # نقطة الدخول: lifespan، CORS، معالجات الأخطاء، /health
│   │   ├── api/              # المعالم (routes): auth, catalog, rag, requests, schedule, broadcasts, notifications
│   │   ├── core/             # الإعدادات (config)، الأمان (JWT/bcrypt)، مصفوفة الصلاحيات
│   │   ├── db/               # engine وsession وأنواع الأعمدة (Vector متعدد قواعد البيانات)
│   │   ├── models/           # نماذج SQLAlchemy: المستخدمون، المواد، الطلبات، الجدول، الرادار، الإشعارات...
│   │   ├── services/
│   │   │   ├── rag/          # ingest → chunks → embeddings → retrieval → tutor/quiz
│   │   │   ├── triage/       # classifier، deduplication، routing، workflow، summarizer، events، visibility
│   │   │   ├── gaps/         # radar + clustering (رادار الفجوات)
│   │   │   ├── schedule/     # snapshot، conflicts، makeup_engine، materialize، read، changes
│   │   │   ├── broadcast/    # hub البلاغات وسجل القراءات
│   │   │   ├── notify/       # خدمة الإشعارات + dispatch
│   │   │   └── common/       # vector_math (NumPy مُتجه)، timeutil
│   │   └── workers/          # celery_app + المهام والمجدول (beat) والأقفال (locks)
│   ├── scripts/              # init_db (إنشاء المخطط) و seed_db (بيانات تجريبية)
│   ├── tests/                # اختبارات وحدات + دورة كاملة عبر الأدوار الخمسة
│   ├── requirements.txt      # الاعتمادات الأساسية
│   ├── requirements-ml.txt   # اعتمادات التضمين المحلي (sentence-transformers)
│   └── .env.example
├── frontend/                 # تطبيق Next.js (App Router)
│   └── src/
│       ├── app/              # الصفحات: login، home، courses/[id]، requests، schedule، broadcasts
│       ├── components/       # AppShell، لوحات المادة (Assistant/Quizzes/Staff)، UnitCard...
│       └── lib/              # api client، stream.ts (قارئ SSE)، auth (جلسة per-tab)، roles، types
├── e2e/                      # اختبارات متصفح حقيقية بـ Playwright
├── deploy/nginx.conf         # وسيط الإنتاج: /api/ → الخلفية، / → الواجهة، دعم SSE
├── docker-compose.yml        # db + redis + migrate + api + worker + beat + web + proxy
└── CHANGELOG-FIXES.md        # سجل الإصلاحات والتحديثات
```

---

## كيف يعمل النظام؟

### 1) الملازم والمساعد (RAG)
1. يرفع المدرس ملف PDF → يُسجَّل Material بحالة `pending` ثم تُناوله مهمة Celery `sdp.ingest_material`: تحميل بالـ pypdf، تقطيع (حجم 1000 / تداخل 150 حرف افتراضياً)، ثم تضمين كل مقطع وحفظه في عمود `Vector`.
2. سؤال الطالب يمر عبر استرجاع دلالي داخل نطاق المادة فقط (لا تسرب بين المواد)، ثم يولّد النموذج إجابة **مقيّدة بالمقاطع المسترجَعة**؛ وإن لم تكفِ المقاطع تكون الإجابة الحرفية: *"هذا الموضوع غير موجود في ملزمة المادة"*.
3. كل سؤال طالب يُخزَّن كـ `StudentQuestion` ليكون لاحقاً مادة لرادار الفجوات.

### 2) رادار الفجوات (Gap Radar)
- مهمة مجدولة (يومياً 02:00) أو تشغيل يدوي من واجهة المدرس.
- يجمع أسئلة الطلاب وأخطاء الكويزات، يجميعها دلالياً حول "مراكز مواضيع" (عتبة تشابه 0.75)، ويطلق **Gap Alert** عندما تتجاوز نسبة الخطأ عتبة 0.30 أو تكرّر السؤال من أكثر من طالب (`gap_min_members=2`)، مع دمج التنبيهات المتشابهة (0.85).
- التنبيه يصل للمدرس (ولرئيس القسم عبر الصلاحية القسمية `gaps:view_department`) ويمكن إقرار الاستلام (acknowledge) من الواجهة.

### 3) دورة حياة الطلب (Triage Workflow)
```
طالب ينشئ طلباً → تصنيف آلي (academic/administrative) بثقة ≥ 0.6
   ├─ أكاديمي  → ممثل الشعبة (مراجعة ودمج المتشابهات دلالياً ≥ 0.85 داخل نفس المادة)
   │              → المدرس (قرار) → مقرر القسم → رئيس القسم (قرار نهائي)
   └─ إداري    → ممثل الشعبة (دمج على مستوى القسم) → مقرر القسم → رئيس القسم
```
- الطلبات المتشابهة تُدمج في **RequestBatch** بتلخيص آلي واحد، والحدث يُسجَّل في Timeline مرئية حسب الدور (`visibility`).
- كشف التكرار عند التقديم يمنع إنشاء طلب مطابق لطلب مفتوح سابق.

### 4) الجدول والتعويضات
- الجدول يُبنى من Pattern → LectureOccurrences (materialize لكل فصل دراسي).
- أي تغيير (قاعة/وقت/إلغاء/تعويض) يمر بفاحص تعارضات (غرف/أساتذة/شعب) ثم يسجَّل في ScheduleChangeLog ويبث فوراً عبر **SSE** (`GET /api/schedule/stream`) لواجهات المستخدمين المفتوحة.
- لإلغاء/تأجيل: محرك التعويض يقترح حتى 5 مواعيد خلال 14 يوماً مستبعداً أياماً محددة (افتراضياً الجمعة)، والمدرس يقبل الاقتراح فيُنشأ Slot بنوع `makeup`.

### 5) البلاغات والإشعارات
- البلاغ له scope (قسم/مادة/شعبة) وقناة؛ القراءة تُسجَّل لكل مستقبل (`BroadcastRead`) ويمكن معرفة من قرأ.
- المهام المجدولة تخطط الإشعارات (ملخص صباحي 07:00 + تذكير قبل المحاضرة بـ 15 دقيقة) ثم توصلها مع حالات pending/sent/failed/cancelled.

---

## تشغيل المشروع

### 1) التشغيل الكامل عبر Docker (موصى به)

```bash
# من جذر المشروع
cp backend/.env.example .env        # ثم عدّل القيم أدناه (على الأقل POSTGRES_PASSWORD و JWT_SECRET_KEY)

export POSTGRES_PASSWORD="غيّر-هذا-كلمة-قوية"
export JWT_SECRET_KEY="سر-عشوائي-طويل-لا-يقل-عن-32-حرفا"
export SEED_DEMO=true               # لتعبئة بيانات تجريبية (اختياري)
# export OPENAI_API_KEY=sk-...      # لتفعيل ميزات الذكاء الاصطناعي الحقيقية (اختياري)

docker compose up -d --build
```

سيتم: إنشاء قاعدة البيانات وامتداد pgvector ← التهيئة/البذر ← تشغيل الـ API والـ Worker والـ Beat ← بناء الواجهة ← النسخ عبر Nginx.

- التطبيق: <http://localhost:8080>
- فحص الصحة: <http://localhost:8080/health>
- وثائق الـ API (Swagger): `http://localhost:8000/docs` عند تشغيل الخلفية مباشرةً (مثلاً بعد `docker compose port api 8000` أو في التطوير المحلي). وسيط Nginx يمرر `/api/` و`/health` فقط، لذا لا تظهر Swagger خلف المنفذ 8080 افتراضياً.

الخدمات في `docker-compose.yml`: `db` (pgvector/pg16) · `redis` · `migrate` (مرة واحدة) · `api` · `worker` · `beat` · `web` · `proxy` (nginx على المنفذ `HTTP_PORT` الافتراضي 8080).

### 2) التشغيل المحلي للتطوير

**الخلفية** (تعمل مع SQLite بدون أي خدمات خارجية):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # الإعدادات الافتراضية مناسبة للتطوير
python -m scripts.seed_db                            # قاعدة SQLite + بيانات تجريبية تلقائياً
uvicorn app.main:app --reload --port 8000
```

> في وضع التطوير تُنفَّذ مهام Celery بشكل متزامن داخل العملية (`CELERY_TASK_ALWAYS_EAGER=true`) فلا حاجة لـ Redis/Worker. وللتضمين الحقيقي محلياً ثبّت أيضاً `pip install -r requirements-ml.txt` وغيّر `EMBEDDING_PROVIDER=huggingface`.

**الواجهة**:

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL="" npm run dev     # أو اضبطها في .env.local على http://localhost:8000
```

فتح <http://localhost:3000> (أو عبر nginx إن توفر).

---

## الحسابات التجريبية

عند تفعيل البذر (`SEED_DEMO=true` أو `python -m scripts.seed_db`) تُنشأ حسابات بكلمة مرور موحدة **`ChangeMe123!`**:

| الدور | البريد |
|---|---|
| رئيس القسم | `head@sdp.local` |
| مقرر القسم | `coord@sdp.local` |
| المدرس | `dr@sdp.local` |
| ممثل الشعبة | `rep@sdp.local` |
| طالب | `student@sdp.local` |

جرّب الدورة كاملة: رفع ملزمة ← سؤال المساعد ← توليد كويز ← إرسال إجابات ← تشغيل الرادار ← تقديم طلب من الطالب ودمجه من الممثل فقرار المدرس فالمقرر فالرئيس ← تغيير جدول ومشاهدة البث الحي.

---

## متغيرات البيئة

تُقرأ من `.env` (راجع `backend/app/core/config.py` و`backend/.env.example`). أهمها:

| المتغير | الافتراضي | الوصف |
|---|---|---|
| `APP_ENV` / `DEBUG` | development / true | بيئة التشغيل ووضع التصحيح |
| `DATABASE_URL` | sqlite:///./sdp_local.db | سلسلة الاتصال؛ للإنتاج `postgresql+psycopg://...` |
| `REDIS_URL` | redis://localhost:6379/0 | وسيط Celery |
| `CELERY_TASK_ALWAYS_EAGER` | false | تنفيذ المهام متزامناً (للتطوير/الاختبار) |
| `JWT_SECRET_KEY` | — | **إلزامي في الإنتاج**، سر توقيع الرموز |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | مدة صلاحية الرمز |
| `EMBEDDING_PROVIDER` | huggingface | `huggingface` \| `openai` \| `stub` (حتمي للاختبارات) |
| `OPENAI_API_KEY` | — | يلزم لمزودي OpenAI (تضمين + LLM) |
| `LLM_MODEL` | gpt-4o-mini | نموذج المحادثة |
| `STORAGE_DIR` | ./storage/materials | مجلد رفع الملفات |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 1000 / 150 | إعدادات تقطيع الملازم |
| `RAG_TOP_K` / `RAG_MIN_SIMILARITY` | 5 / 0.35 | إعدادات الاسترجاع |
| `GAP_*` (threshold/cluster/min_members/merge) | 0.30 / 0.75 / 2 / 0.85 | عتبات رادار الفجوات |
| `REQUEST_DEDUP_SIMILARITY` / `REQUEST_CLASSIFICATION_MIN_CONFIDENCE` | 0.85 / 0.6 | عتبات تصنيف ومعالجة الطلبات |
| `MAKEUP_SEARCH_DAYS` / `MAKEUP_MAX_SUGGESTIONS` / `MAKEUP_EXCLUDED_WEEKDAYS` | 14 / 5 / 4 | محرك التعويضات (4 = الجمعة) |
| `LECTURE_REMINDER_MINUTES` / `MORNING_DIGEST_HOUR` / `TIMEZONE` | 15 / 7 / Asia/Baghdad | الإشعارات والتوقيت |
| `CORS_ORIGINS` | http://localhost:3000 | أصول مسموحة (فاصلة) |

---

## معالم الـ API

كل المسارات تحت `/api` وتتطلب رمز JWT (Bearer) ما عدا `/api/auth/login` و`/health`.

| المجموعة | أبرز النقاط |
|---|---|
| Auth | `POST /login` · `GET /me` |
| Catalog | `GET /courses` · `GET /rooms` |
| RAG | `POST /courses/{id}/materials` (رفع، 202) · `GET /materials/{id}` (حالة المعالجة) · `POST /courses/{id}/ask` · `POST /courses/{id}/summary` · `POST /courses/{id}/quizzes` · `POST /quizzes/{id}/publish` · `POST /quizzes/{id}/attempts` |
| Gaps | `GET /courses/{id}/gaps` · `POST /courses/{id}/gaps/run` · `POST /gaps/{alert_id}/acknowledge` |
| Requests | `POST /requests` · `GET /requests/mine|section|inbox` · `GET /requests/{id}` + `/timeline` · `POST /requests/{id}/classify` · `POST /requests/{id}/actions` (forward/approve/reject/resolve...) · `POST /batches/{id}/actions` · `POST /sections/consolidate` · `POST /batches/{id}/refresh-summary` |
| Schedule | `GET /week` · `GET /changes` · `GET /stream` (SSE) · `POST /occurrences/{id}/room|reschedule|cancel` · `POST /makeup/suggest` · `POST /makeup/suggestions/{id}/accept` · `POST /semesters/{id}/materialize` |
| Broadcasts | `POST /api/broadcasts` · `GET /api/broadcasts` · `POST /{id}/read` · `GET /{id}/readers` |
| Notifications | `GET /api/notifications/mine` |

ملاحظة: الوصول محدود دائماً بالنطاق — الطالب يرى شعبته، المدرس موادّه، والمقرر/الرئيس القسم.

---

## المهام المجدولة (Celery Beat)

| المهمة | الجدول | الوظيفة |
|---|---|---|
| `sdp.run_gap_radar` | يومياً 02:00 | إعادة تجميع الفجوات وإطلاق التنبيهات |
| `sdp.plan_notifications` | كل دقيقة | توليد الملخص الصباحي وتذكيرات ما قبل المحاضرة |
| `sdp.dispatch_notifications` | كل دقيقة | تسليم الإشعارات المخططة |
| `sdp.ingest_material` | عند الطلب (غير مجدولة) | معالجة ملزمة مرفوعة (تقطيع + تضمين) |

مهام الرادار والتنبيهات محمية بأقفال Redis (`app/workers/locks.py`) لمنع التكرار عند تعدد الـ Workers.

---

## الاختبارات

```bash
# اختبارات الخلفية (72 اختباراً: وحدات + دورة كاملة عبر الأدوار + RAG + رادار + جدول + بلاغات)
cd backend
pip install -r requirements.txt
pytest -q

# فحص أنواع وبناء الواجهة
cd ../frontend
npm run typecheck
npm run build

# اختبارات المتصفح الحقيقية (Playwright) — تتطلب تشغيل الخلفية (8000) والواجهة (3000) أولاً
cd ../e2e
pip install -r requirements.txt
playwright install chromium
E2E_BASE_URL=http://localhost:3000 pytest tests -q
```

الاختبارات تستخدم التضمين `stub` ولا تحتاج مفاتيح خارجية؛ وتغطي أيضاً مسارات الاحتياط عند غياب `OPENAI_API_KEY`.

---

## ملاحظات تشغيلية

- **ميزات الذكاء الاصطناعي** (المساعد، الكويزات، التصنيف، التلخيص) تحتاج `OPENAI_API_KEY` في الإنتاج؛ بدونها تعمل أنظمة احتياط وصفية بدلاً من النموذج.
- **pgvector**: نوع `Vector` في `app/db/types.py` يعمل على PostgreSQL (امتداد vector) وSQLite (تمثيل JSON) بنفس الكود — لذا التطوير لا يتطلب قاعدة خارجية.
- **المخطط**: حالياً يُنشأ عبر `scripts/init_db.py` (create_all). قبل الإنتاج ثبّت المخطط بأنشاء مراجعة Alembic أولى (`alembic revision --autogenerate -m "initial"` ثم `upgrade head`) وبدّل أمر خدمة migrate كما هو موثق داخل السكربت.
- **الأمان**: كلمة المرور تُخزَّن bcrypt، والجلسات JWT قصيرة الأمد. في الواجهة تُحفظ الجلسة في `sessionStorage` (جلسة مستقلة لكل تبويب — وهذا سبب إصلاح أخطاء 403 الموثق في `CHANGELOG-FIXES.md`). بدّل `JWT_SECRET_KEY` الافتراضي قبل أي نشر.
- **SSE عبر Nginx**: تم تعطيل التخزين المؤقت للـ buffering في `deploy/nginx.conf` ليصل بث تغييرات الجدول لحظياً.
- **الفهارس والأداء**: فهارس مركبة على الجداول الساخنة (clusters/alerts/occurrences...)، وعمليات المتجهات مصفوفية بالكامل عبر NumPy (`services/common/vector_math.py`)، وأحواض اتصال مضبوطة (PostgreSQL) وWAL لـ SQLite.
- **منطقة زمنية**: كل المواعيد تخزن UTC وتعرض بتوقيت `Asia/Baghdad`.

---

## راجع أيضاً

- [CHANGELOG-FIXES.md](CHANGELOG-FIXES.md) — سجل الإصلاحات الجذرية ونتائج التشغيل الأخيرة.
- `backend/.env.example` — نموذج كامل لمتغيرات البيئة.
