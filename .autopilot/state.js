window.STATE =
{
  "slug": "onam-shop",
  "dir": "2026-09-27-onam-shop--wip",
  "title": "Faberlik Sotuv Bot — Telegram Mini App do'koni",
  "mode": "full",
  "depth": "normal",
  "polish": null,
  "tier": "T2",
  "briefFile": "2026-09-27-brief.md",
  "memoryFile": "CLAUDE.md",
  "skillDir": "C:/Users/user/.claude/skills/autopilot",
  "startedAt": "2026-09-27T15:46:43+05:00",
  "updatedAt": "2026-09-27T16:11:41+05:00",
  "finishedAt": null,
  "stages": [
    {
      "id": "preflight",
      "status": "done",
      "startedAt": "2026-09-27T15:46:43+05:00",
      "finishedAt": "2026-09-27T15:49:23+05:00"
    },
    {
      "id": "manifest",
      "status": "done",
      "startedAt": "2026-09-27T15:49:23+05:00",
      "finishedAt": "2026-09-27T15:49:23+05:00"
    },
    {
      "id": "briefing",
      "status": "skipped",
      "note": "полный автомат — самобрифинг",
      "startedAt": "2026-09-27T15:49:23+05:00",
      "finishedAt": "2026-09-27T15:49:23+05:00"
    },
    {
      "id": "spec",
      "status": "active",
      "startedAt": "2026-09-27T15:49:23+05:00"
    },
    {
      "id": "plan",
      "status": "pending"
    },
    {
      "id": "build",
      "status": "pending"
    },
    {
      "id": "review",
      "status": "pending"
    },
    {
      "id": "final",
      "status": "pending"
    }
  ],
  "requirements": {
    "total": 71,
    "done": 0,
    "inTicket": 60,
    "inSpec": 11,
    "placeholder": 0,
    "deferred": 0,
    "dropped": 0
  },
  "tickets": [
    {
      "id": "01",
      "startedAt": "2026-09-27T16:01:51+05:00",
      "title": "Backend asosi: sozlamalar, DB, migratsiya, initData auth, /health",
      "requirements": [
        "R10",
        "R16",
        "R17",
        "R48",
        "R49",
        "R50",
        "R51",
        "R68",
        "R08"
      ],
      "blockedBy": [],
      "wave": 1,
      "zone": [
        "backend/"
      ],
      "status": "review",
      "retries": 0,
      "repairs": 0,
      "handoffs": 0
    },
    {
      "id": "02",
      "title": "Katalog API, admin mahsulot/kategoriya CRUD, rasm yuklash, rate limit, seed",
      "requirements": [
        "R20",
        "R21",
        "R22",
        "R42",
        "R43",
        "R44",
        "R45",
        "R47",
        "R52",
        "R53",
        "R09",
        "R51"
      ],
      "blockedBy": [
        "01"
      ],
      "wave": 2,
      "zone": [
        "backend/app/services/catalog",
        "backend/app/uploads",
        "backend/app/api/catalog"
      ],
      "status": "pending",
      "retries": 0,
      "repairs": 0,
      "handoffs": 0
    },
    {
      "id": "03",
      "title": "Zakaz xizmati: yaratish, status mashinasi, tarix, mijoz va admin zakaz API, statistika, Notifier porti",
      "requirements": [
        "R01",
        "R02",
        "R03",
        "R25",
        "R26",
        "R27",
        "R28",
        "R39",
        "R46",
        "R51",
        "R52",
        "R53",
        "R69i",
        "R70i",
        "R71i"
      ],
      "blockedBy": [
        "02"
      ],
      "wave": 3,
      "zone": [
        "backend/app/services/orders",
        "backend/app/api/orders"
      ],
      "status": "pending",
      "retries": 0,
      "repairs": 0,
      "handoffs": 0
    },
    {
      "id": "04",
      "title": "Ikki bot (aiogram), TelegramNotifier, eslatmalar, kunlik hisobot, lifespan",
      "requirements": [
        "R02",
        "R03",
        "R08",
        "R10",
        "R17",
        "R18",
        "R19",
        "R30",
        "R31",
        "R32",
        "R33",
        "R34",
        "R35",
        "R36",
        "R37",
        "R38",
        "R39",
        "R40",
        "R41",
        "R70i"
      ],
      "blockedBy": [
        "03"
      ],
      "wave": 4,
      "zone": [
        "backend/app/bots/",
        "backend/app/scheduler"
      ],
      "status": "pending",
      "retries": 0,
      "repairs": 0,
      "handoffs": 0
    },
    {
      "id": "05",
      "title": "Frontend asosi + mijoz Mini App (/app)",
      "requirements": [
        "R04",
        "R05",
        "R11",
        "R12",
        "R13",
        "R20",
        "R21",
        "R22",
        "R23",
        "R24",
        "R25",
        "R26",
        "R27",
        "R28",
        "R29",
        "R45",
        "R48",
        "R53"
      ],
      "blockedBy": [
        "01"
      ],
      "wave": 2,
      "zone": [
        "frontend/"
      ],
      "status": "in-progress",
      "startedAt": "2026-09-27T16:09:52+05:00",
      "retries": 0,
      "repairs": 0,
      "handoffs": 0
    },
    {
      "id": "06",
      "title": "Admin Mini App (/admin)",
      "requirements": [
        "R12",
        "R13",
        "R29",
        "R42",
        "R43",
        "R44",
        "R45",
        "R46",
        "R50"
      ],
      "blockedBy": [
        "05"
      ],
      "wave": 3,
      "zone": [
        "frontend/src/admin/"
      ],
      "status": "pending",
      "retries": 0,
      "repairs": 0,
      "handoffs": 0
    },
    {
      "id": "07",
      "title": "E2E (Playwright + mock Telegram), Docker/Caddy fayllari, README (uz)",
      "requirements": [
        "R05",
        "R08",
        "R14",
        "R15",
        "R59",
        "R63",
        "R64",
        "R65",
        "R67"
      ],
      "blockedBy": [
        "04",
        "06"
      ],
      "wave": 5,
      "zone": [
        "frontend/e2e/",
        "Dockerfile",
        "README.md"
      ],
      "status": "pending",
      "retries": 0,
      "repairs": 0,
      "handoffs": 0
    }
  ],
  "singlePass": null,
  "tests": null,
  "debt": {
    "placeholders": [
      "S05 — адрес самовывоза (PICKUP_ADDRESS)",
      "S23 — цены seed-товаров — образцы"
    ],
    "assumptions": [
      "S01–S23 — самобрифинг, см. manifest.md / docs/DECISIONS.md"
    ],
    "emptyEnv": [
      "CUSTOMER_BOT_TOKEN",
      "ADMIN_BOT_TOKEN",
      "ADMIN_IDS",
      "WEBAPP_URL",
      "DOMAIN",
      "PICKUP_ADDRESS"
    ]
  },
  "additions": [
    "A01 — TELEGRAM_API_BASE для мок-сервера Telegram в E2E (ради R59)"
  ],
  "coverage": {
    "findings": 22,
    "missing": 14,
    "half": 7,
    "extra": "~45 deepening items (R##.n) + A01",
    "action": "process rules copied into spec Процесс; retry wording corrected; extras are deepening of brief rows, kept"
  },
  "concerns": [
    "backend/app/models.py — naive DateTime columns (UTC by convention, re-attach tz on read)",
    "backend/app/main.py:14 — include_routers hook not in spec seam table (internal, recorded in interfaces.md)",
    "backend/app/auth.py:103-125 — customer_user/admin_user duplicate validate+except shape",
    "backend/app/config.py:39-40 — malformed ADMIN_IDS raises bare ValueError",
    "backend/app/models.py — no round-trip test that tz survives on DateTime columns"
  ],
  "reviewers": {
    "manifestSpec": "ad63e74d060485c43",
    "craft": "aa698c67331c31f86"
  },
  "blind": null
}
