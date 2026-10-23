# Лабораторная работа 2. Потоковый анализатор файлов

`streamstats` читает события из CSV и JSONL по одной записи и пишет один отчёт в JSON или CSV. Несколько файлов одного формата складываются в общие счётчики.

## Окружение

```bash
uv sync
```

Команды ниже запускаются через `uv run`: так подхватываются `pydantic`, `loguru`, `pytest` и `ruff`.

## Запуск

```bash
uv run python -m streamstats analyze examples/events.jsonl \
  --format jsonl --output report.json

uv run python -m streamstats analyze examples/events.csv \
  --format csv --report-format csv --output report.csv
```

```bash
uv run python -m streamstats analyze a.jsonl b.jsonl \
  --format jsonl --skip-invalid
```

`--format` один на весь запуск. Встроенные имена: `csv` и `jsonl`. `--report-format` выбирает вид отчёта, по умолчанию `json`. Без `--output` отчёт печатается в stdout.

Битая строка останавливает чтение до записи отчёта. В stderr попадают путь к файлу и номер строки, код выхода -- `2`. `--skip-invalid` пропускает такую строку, пишет `WARNING` через loguru и увеличивает `skipped_lines`.

## Событие

CSV начинается со строки `timestamp,level,source,message`. В JSONL каждая строка -- отдельный JSON-объект.

- `timestamp` -- ISO 8601 с часовым поясом. Метка без пояса отклоняется. В отчёте время приведено к UTC, поэтому `2026-10-19T10:00:00Z` записывается как `2026-10-19T10:00:00+00:00`.
- `level` -- `DEBUG`, `INFO`, `WARNING`, `ERROR` или `CRITICAL`.
- `source` -- непустая строка. Строка из одних пробелов тоже отклоняется.
- `message` -- любая строка, в том числе пустая.

Пустая строка JSONL считается битой записью.

## Пример

В `examples/events.jsonl` пять событий. У `database` два из них ошибочные: одно `ERROR` и одно `CRITICAL`.

```bash
uv run python -m streamstats analyze examples/events.jsonl \
  --format jsonl --output report.json
```

```json
{
  "total_events": 5,
  "levels": {
    "DEBUG": 0,
    "INFO": 2,
    "WARNING": 1,
    "ERROR": 1,
    "CRITICAL": 1
  },
  "sources": {
    "api": 2,
    "auth": 1,
    "database": 2
  },
  "top_error_sources": [
    {"source": "database", "count": 2}
  ],
  "first_timestamp": "2026-10-19T10:00:00+00:00",
  "last_timestamp": "2026-10-19T10:04:00+00:00",
  "skipped_lines": 0
}
```

`levels` всегда содержит все пять уровней. `sources` -- только встретившиеся источники, по алфавиту. `first_timestamp` и `last_timestamp` -- самая ранняя и самая поздняя метка среди всех файлов. У пустого входа метки равны `null`, счётчики нулевые, файл отчёта всё равно создаётся.

В `top_error_sources` попадают не больше пяти источников с наибольшей суммой `ERROR` и `CRITICAL`. Остальные уровни в эту сумму не входят. В примере такая сумма есть только у `database`, и она равна 2.

`skipped_lines` есть в каждом отчёте. В обычном режиме там `0`: битая строка прерывает запуск раньше записи файла.

## Ошибки

Ожидаемые сбои -- наследники `StreamStatsError`. Текст пишет loguru в stderr, процесс завершается с кодом `2`.

| Ситуация | Исключение |
| --- | --- |
| Неверный уровень, пустой `source`, пустая строка JSONL, сломанный JSON | `InvalidEventError` |
| Метка не в ISO 8601 или без часового пояса | `InvalidTimestampError` |
| `--format` не зарегистрирован | `UnsupportedFormatError` |
| `--report-format` не `json` и не `csv` | `UnsupportedFormatError` |
| Входного файла нет, `--output` указывает на каталог или на несуществующую папку | `CLIConfigError` |

У `InvalidEventError` и `InvalidTimestampError` в тексте есть путь к файлу и номер строки. Файл не в UTF-8 и прочая ошибка чтения тоже завершают процесс с кодом `2`.

## Модули

- `models.py` описывает событие и обязательные поля.
- `validation.py` разбирает уровень, метку времени и `source`.
- `enums.py` задаёт пять уровней.
- `parsers/csv_parser.py` читает CSV с заголовком, запись за записью.
- `parsers/jsonl_parser.py` читает JSONL, строка за строкой.
- `parsers/common.py` проверяет запись и решает, остановить чтение или пропустить строку.
- `analysis.py` держит один набор счётчиков на все файлы и реестр парсеров.
- `report.py` переводит уже посчитанную статистику в JSON или CSV.
- `errors.py` содержит иерархию ошибок.
- `constants.py` хранит код выхода, лимит top-5 и уровни, которые считаются ошибочными.
- `cli.py` разбирает аргументы, проверяет пути и возвращает код выхода.
- `__main__.py` только запускает `main`, когда пакет вызван как программа.

## Дополнительные задания

Сделаны два пункта.

Реестр парсеров. `register_parser(name, parser)` добавляет входной формат. Функция читает один путь и отдаёт события по одному, с аргументами `path`, `skip_invalid` и `skipped`, как `parse_csv`. Имена `csv` и `jsonl` регистрируются при импорте. `analyze_files` и `--format` берут функцию из этого реестра, поэтому свой формат доступен в том же процессе после регистрации. Повторная регистрация того же имени заменяет функцию. `unregister_parser` убирает её.

CSV-отчёт. `--report-format csv` записывает те же счётчики, что и JSON. Оба формата рендерят один результат `build_report`, входные файлы второй раз не читаются. Столбцы: `section`, `name`, `value`. Для примера выше начало файла такое:

```csv
section,name,value
summary,total_events,5
summary,skipped_lines,0
summary,first_timestamp,2026-10-19T10:00:00+00:00
summary,last_timestamp,2026-10-19T10:04:00+00:00
level,DEBUG,0
level,INFO,2
```

## Проверка

```bash
uv run pytest
uv run ruff check .
uv run python -m streamstats --help
```
