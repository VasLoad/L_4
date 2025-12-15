import re
from urllib.parse import quote

from config import URL_QUOTE_REGEX
from enums.payload_command import PayloadCommand


def generate_content_share_url(payload_command: PayloadCommand, content_id: str) -> str:
    url = f"https://t.me/TrackStarInfo_bot?start={payload_command.value}"

    data = f"_{quote(content_id)}"

    data = re.sub(URL_QUOTE_REGEX, "", data)

    url += data

    return url
