# quantviews

Личный аналитический сайт Марселя Салихова: экономика, данные, финансы и
аналитические системы. Собран на [Quarto](https://quarto.org), публикуется на
GitHub Pages.

Сайт: <https://quantviews.github.io/>

## Разделы

| Раздел | Источник | Как устроен |
|---|---|---|
| Блог | `posts/` | Quarto listing, RSS в `posts.xml` |
| Проекты | `projects.qmd`, `projects/` | Карточки + сводная таблица |
| Преподавание | `courses.qmd`, `courses/` | Курсы и учебные материалы |
| Выступления | `talks/` | Quarto listing (grid) |
| Комментарии в СМИ | `media/` | Quarto listing |
| Технические заметки | `notes/` | Заметки по инструментам |
| Об авторе | `about.qmd` | — |

## Оформление

- `_brand.yml` — палитра, шрифты, логотип (Quarto brand).
- `styles.scss` — правила, компилируемые вместе с темой (основное место для стилей).
- `styles.css` — правила, подключаемые после темы; используется для точечных
  переопределений, которых нельзя добиться в `styles.scss`.

Темы: `cosmo` (светлая) и `darkly` (тёмная).

## Локальная разработка

```bash
quarto preview     # живой предпросмотр
quarto render      # сборка в _site/
```

Выполнение кода в документах отключено (`execute: enabled: false`) — `.qmd`
рендерятся как разметка.

## Новый пост

```
posts/YYYY-MM-DD-latinskiy-slug/
  index.qmd
  images/            # изображения поста лежат рядом с ним
```

Обязательные поля frontmatter: `title`, `date`, `author`, `categories`,
`description`. Слаги — латиницей: посты, перенесённые с Blogspot, сохраняют
старые кириллические адреса через `aliases:`, поэтому такие поля трогать не нужно.

## Публикация

- `.github/workflows/publish.yml` — рендер и деплой в ветку `gh-pages` при push в `main`.
- `.github/workflows/telegram.yml` — анонс нового поста в [@quantviews](https://t.me/quantviews).
  Требует секрет `TELEGRAM_BOT_TOKEN`; ручной запуск отправляет тестовое сообщение.

## Служебные скрипты

Разовые инструменты миграции с Blogspot, в обычной работе не нужны:

| Скрипт | Назначение |
|---|---|
| `scripts/migrate_blogspot.py` | выгрузка постов из Blogspot в `.qmd` |
| `scripts/fix_yaml.py`, `scripts/fix_migrated_posts.py` | правка frontmatter после выгрузки |
| `scripts/fix_descriptions.py` | перегенерация полей `description` |
| `scripts/transliterate_slugs.py` | латинские слаги + `aliases` на старые адреса |
| `scripts/tidy_frontmatter.py` | нормализация `title` / `description` / `aliases` |
| `scripts/retry_wayback.py` | повторная попытка вытащить недоступные картинки из Wayback Machine |
