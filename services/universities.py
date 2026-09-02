UNIVERSITY_OPTIONS = (
    ("uni_kfu", "КФУ", "🏛"),
    ("uni_knitu", "КНИТУ", "🧪"),
    ("uni_knitu_kai", "КНИТУ-КАИ", "✈️"),
    ("uni_kgmu", "КГМУ", "⚕️"),
    ("uni_kgeu", "КГЭУ", "⚡"),
    ("uni_kgasu", "КГАСУ", "🏗"),
    ("uni_kgau", "КГАУ", "🌾"),
    ("uni_vguyu", "ВГУЮ", "⚖️"),
    ("uni_kf_rgup", "КФ РГУП", "⚖️"),
    ("uni_tisbi", "ТИСБИ", "🎓"),
    ("uni_pgufksit", "ПГУФКСиТ", "🏅"),
    ("uni_kazgik", "КазГИК", "🎭"),
)

UNIVERSITIES_BY_CALLBACK = {
    callback_data: name
    for callback_data, name, _emoji in UNIVERSITY_OPTIONS
}

UNIVERSITY_NAMES = tuple(
    name
    for _callback_data, name, _emoji in UNIVERSITY_OPTIONS
)
