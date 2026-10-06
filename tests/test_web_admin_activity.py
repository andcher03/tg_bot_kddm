from services.web_admin_activity import device_summary, section_name


def test_device_summary_identifies_common_mobile_browser():
    user_agent = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
        "Mobile/15E148 Safari/604.1"
    )
    assert device_summary(user_agent) == "Телефон · iOS · Safari"


def test_device_summary_identifies_edge_on_windows_desktop():
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 "
        "Safari/537.36 Edg/132.0.0.0"
    )
    assert device_summary(user_agent) == "Компьютер · Windows · Edge"


def test_section_name_groups_admin_paths_without_query_parameters():
    assert section_name("/events/52/edit") == "Мероприятия"
    assert section_name("/service-admin") == "Администрирование сервиса"
    assert section_name("/unknown") == "Веб-админка"
