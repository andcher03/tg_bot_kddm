from dataclasses import dataclass
from pathlib import Path


QUIZ_CODE = "kazan_anomalies_2026"
QUIZ_TITLE = "Какая ты аномалия Казани?"
QUIZ_IMAGE_DIR = (
    Path(__file__).resolve().parent.parent
    / "web_admin"
    / "static"
)

ROUTE = "route"
BACKROOMS = "backrooms"
STATION = "station"
SONG = "song"
LAKE = "lake"
TUBETEIKA = "tubeteika"

RESULT_ORDER = (
    ROUTE,
    BACKROOMS,
    STATION,
    SONG,
    LAKE,
    TUBETEIKA,
)


@dataclass(frozen=True)
class QuizOption:
    text: str
    results: tuple[str, ...]


@dataclass(frozen=True)
class QuizQuestion:
    text: str
    options: tuple[QuizOption, ...]


@dataclass(frozen=True)
class QuizResult:
    title: str
    description: str
    image_filename: str


QUESTIONS = (
    QuizQuestion(
        text="Ваше любимое животное?",
        options=(
            QuizOption("Кошки", (ROUTE, BACKROOMS)),
            QuizOption("Собаки", (TUBETEIKA, STATION)),
            QuizOption("Птицы", (SONG,)),
            QuizOption("Всех люблю", (LAKE,)),
        ),
    ),
    QuizQuestion(
        text="Ваш темперамент?",
        options=(
            QuizOption("Холерик", (TUBETEIKA,)),
            QuizOption("Сангвиник", (SONG,)),
            QuizOption("Меланхолик", (ROUTE,)),
            QuizOption("Флегматик", (LAKE,)),
            QuizOption("Всего понемногу", (BACKROOMS,)),
            QuizOption("Ничего из этого", (STATION,)),
        ),
    ),
    QuizQuestion(
        text="Ваши ценности в жизни?",
        options=(
            QuizOption("Семья и близкие", (ROUTE,)),
            QuizOption("Любовь", (LAKE,)),
            QuizOption("Работа", (BACKROOMS,)),
            QuizOption("Статус в обществе", (TUBETEIKA,)),
            QuizOption("Я сам", (STATION,)),
            QuizOption("Творчество", (SONG,)),
        ),
    ),
    QuizQuestion(
        text="Как вы проведёте свой выходной?",
        options=(
            QuizOption("Отдохну дома", (BACKROOMS,)),
            QuizOption("Встречусь с друзьями", (ROUTE,)),
            QuizOption("Съезжу на дачу", (TUBETEIKA,)),
            QuizOption("Пойду гулять в парк", (LAKE,)),
            QuizOption(
                "Культурная программа в городе",
                (SONG,),
            ),
            QuizOption("Съезжу в соседний город", (STATION,)),
        ),
    ),
    QuizQuestion(
        text="Какую роль в компании вы занимаете?",
        options=(
            QuizOption("Организую встречи", (TUBETEIKA,)),
            QuizOption("Шучу шутки", (SONG,)),
            QuizOption("Слушаю разговоры", (LAKE,)),
            QuizOption("Предлагаю активности", (STATION,)),
            QuizOption(
                "Часто пропадаю из-за занятости",
                (ROUTE,),
            ),
            QuizOption("Спорю", (BACKROOMS,)),
        ),
    ),
    QuizQuestion(
        text="Какую музыку слушаете?",
        options=(
            QuizOption("Поп", (LAKE,)),
            QuizOption("Рэп", (BACKROOMS,)),
            QuizOption("Рок", (TUBETEIKA,)),
            QuizOption("R&B", (STATION,)),
            QuizOption("Всего понемногу", (SONG,)),
            QuizOption("То, что сейчас в тренде", (ROUTE,)),
        ),
    ),
    QuizQuestion(
        text="Как вы относитесь к дедлайнам?",
        options=(
            QuizOption("Когда-нибудь сяду", (ROUTE,)),
            QuizOption("Делаю заранее", (STATION,)),
            QuizOption("Делаю точно к сроку", (TUBETEIKA,)),
            QuizOption(
                "Волнуюсь и начинаю поздно",
                (LAKE,),
            ),
            QuizOption(
                "Забываю и делаю в последний момент",
                (SONG,),
            ),
            QuizOption(
                "Сначала долго продумываю план",
                (BACKROOMS,),
            ),
        ),
    ),
)


RESULTS = {
    ROUTE: QuizResult(
        title="«Маршрут» — автобус, который всегда приезжает вовремя",
        image_filename="route.png",
        description=(
            "Вы добрый, ответственный, немного тревожный человек. "
            "Вы часто бываете заняты, и поэтому редко видитесь с "
            "друзьями, но вы всегда готовы подъехать к любой тусовке, "
            "на которую они вас позовут. Иногда устраиваете себе дни "
            "проверки выполненной работы?"
        ),
    ),
    BACKROOMS: QuizResult(
        title="Бэкрумс на станции «Проспект Победы»",
        image_filename="avenue.png",
        description=(
            "Вы постоянно находитесь в движении. Один вариант решения "
            "вопроса вас редко когда устроит — вы придумаете много "
            "сценариев на любой случай. Иногда не стоит думать слишком "
            "глубоко)"
        ),
    ),
    STATION: QuizResult(
        title="Третий Казанский вокзал",
        image_filename="railway.png",
        description=(
            "Вы не сидите на месте и придумываете новые маршруты, чтобы "
            "дойти из точки А в точку Б нескучным способом. Любите "
            "узнавать новое и тянетесь к путешествиям. В любом случае "
            "Казань всегда рада вас видеть!"
        ),
    ),
    SONG: QuizResult(
        title="Бесконечная песня на Баумана",
        image_filename="musicians.png",
        description=(
            "Вы творческий человек с хорошим вкусом. Вам важна свобода "
            "мысли и поток создания чего-то. У вас большой потенциал, "
            "не останавливайтесь на достигнутом! Уверены, у вас много "
            "упорства."
        ),
    ),
    LAKE: QuizResult(
        title="Среднее Чайковое озеро",
        image_filename="lake.png",
        description=(
            "Вы человек достаточно простой, и вам многого не надо. "
            "Любите побыть в тишине и на природе. При этом цените порядок "
            "и много времени проводите в размышлениях обо всём. Знаете, "
            "что вам нужен отдых, и очень цените это время."
        ),
    ),
    TUBETEIKA: QuizResult(
        title="Тюбетейка на Московском рынке",
        image_filename="tubeteika.png",
        description=(
            "Вы любите порядок и хотите, чтобы всё было по-вашему. "
            "При этом вы очень упорно добиваетесь порядка. Цените связи "
            "с людьми и защищаете близких. Любите отдых за городом."
        ),
    ),
}


# При равенстве баллов сначала учитываются ответы на самые содержательные
# вопросы: ценности, роль в компании и отношение к дедлайнам.
TIE_BREAK_QUESTION_ORDER = (2, 4, 6, 1, 3, 5, 0)


def calculate_result(answer_indexes: list[int]) -> str:
    if len(answer_indexes) != len(QUESTIONS):
        raise ValueError("Нужно ответить на все вопросы теста.")

    scores = {result_id: 0 for result_id in RESULT_ORDER}

    for question, option_index in zip(
        QUESTIONS,
        answer_indexes,
        strict=True,
    ):
        if not 0 <= option_index < len(question.options):
            raise ValueError("Получен неизвестный вариант ответа.")

        option = question.options[option_index]

        for result_id in option.results:
            scores[result_id] += 1

    best_score = max(scores.values())
    leaders = {
        result_id
        for result_id, score in scores.items()
        if score == best_score
    }

    if len(leaders) == 1:
        return next(iter(leaders))

    for question_index in TIE_BREAK_QUESTION_ORDER:
        option = QUESTIONS[question_index].options[
            answer_indexes[question_index]
        ]
        matching = leaders.intersection(option.results)
        if len(matching) == 1:
            return next(iter(matching))

    return next(
        result_id
        for result_id in RESULT_ORDER
        if result_id in leaders
    )


def format_result(result_id: str) -> str:
    result = RESULTS[result_id]
    return (
        f"🎭 <b>Ваш результат: {result.title}</b>\n\n"
        f"{result.description}"
    )


def result_image_path(result_id: str) -> Path:
    return QUIZ_IMAGE_DIR / RESULTS[result_id].image_filename
