def convert_time_from_milliseconds(milliseconds: int) -> str:
    """Конвертер времени из мсек. в чч:мм:сс."""
    
    result_time_str = ""

    seconds = milliseconds // 1000

    minutes = seconds // 60
    seconds %= 60

    hours = minutes // 60
    minutes %= 60

    hours_str = f"{hours}:" if hours > 0 else ""
    minutes_str = f"{minutes}:" if minutes > 0 else ""
    seconds_str = f"{seconds}" if seconds > 0 else ""

    if hours_str:
        result_time_str += hours_str
    if minutes_str:
        result_time_str += minutes_str
    else:
        if hours_str:
            minutes_str = "00:"

            result_time_str += minutes_str
    if seconds_str:
        result_time_str += seconds_str
    else:
        if minutes_str:
            seconds_str = "00"

            result_time_str += seconds_str

    if not minutes_str and seconds_str:
        result_time_str += " сек."

    if result_time_str == "":
        if milliseconds > 0:
            result_time_str = f"{milliseconds} мсек."
        else:
            result_time_str = "Отсутствует"

    return result_time_str
