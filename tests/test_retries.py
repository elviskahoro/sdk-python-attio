import httpx2 as httpx

from attio.utils.retries import _is_transport_error


def test_is_transport_error_matches_httpx_network_error():
    assert _is_transport_error(httpx.ConnectError("boom"))


def test_is_transport_error_matches_httpx_timeout():
    assert _is_transport_error(httpx.ReadTimeout("boom"))


def test_is_transport_error_rejects_unrelated_exception():
    assert not _is_transport_error(ValueError("boom"))


def test_is_transport_error_rejects_same_named_third_party_class():
    class NetworkError(Exception):
        pass

    assert not _is_transport_error(NetworkError("boom"))


def test_is_transport_error_matches_httpx2_like_module():
    # Simulate httpx2 (Pydantic's httpx fork, see README's alias_httpx()
    # section) without requiring the package to be installed: build a class
    # whose MRO mirrors httpx's transport-error hierarchy but reports a
    # different (httpx2-prefixed) module.
    class HTTPError(Exception):
        pass

    class RequestError(HTTPError):
        pass

    class TransportError(RequestError):
        pass

    class NetworkError(TransportError):
        pass

    for cls in (HTTPError, RequestError, TransportError, NetworkError):
        cls.__module__ = "httpx2._exceptions"

    assert _is_transport_error(NetworkError("boom"))
