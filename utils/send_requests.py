import requests
from typing import Any, Optional

from requests import Response

from enums.request_type import RequestType
from errors import RemoteResponseDataError, RemoteTimeoutError, RemoteConnectionError, RemoteHTTPError, \
    RemoteRequestException


def send_request(
        request_type: RequestType,
        url: str,
        headers: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        timeout: int = 250
) -> Response:
    """
    Отправляет POST/GET-запрос по указанному URL.

    Args:
        request_type: Тип запроса
        url: URL для отправки запроса
        headers: Заголовки
        data: Данные для POST-запроса
        params: Данные для GET-запроса
        timeout: Время ожидания

    Returns:
        Ответ в виде объекта requests.Response

    Raises:
        RemoteTimeoutError: Превышено время ожидания
        RemoteConnectionError: Ошибка подключения
        RemoteHTTPError: Ошибка HTTP-запроса
        RemoteRequestException: Ошибка запроса
        RemoteResponseDataError: Некорректные данные в ответе
    """

    try:
        if request_type == RequestType.POST:
            response: Response = requests.post(
                url=url,
                headers=headers,
                data=data,
                timeout=timeout
            )
        else:
            response: Response = requests.get(
                url=url,
                headers=headers,
                params=params,
                timeout=timeout
            )

        response.raise_for_status()

        return response

    except requests.exceptions.Timeout:
        raise RemoteTimeoutError()

    except requests.exceptions.ConnectionError:
        raise RemoteConnectionError()

    except requests.exceptions.HTTPError as ex:
        raise RemoteHTTPError(ex)

    except requests.exceptions.RequestException as ex:
        raise RemoteRequestException(str(ex))

    except Exception as ex:
        raise RemoteResponseDataError(str(ex))
