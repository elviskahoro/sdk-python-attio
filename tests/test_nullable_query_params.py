"""Regression tests for nullable GET query-parameter three-state behavior.

Nullable GET query params are generated as ``OptionalNullable[T] = UNSET``:
  - ``UNSET`` (omitted)  -> param NOT sent on the wire
  - ``None`` (explicit)  -> depends on the parameter's contract:
    - for params that document an empty/null filter (e.g. ``assignee``), the
      call site passes ``allow_empty_value=[...]`` so ``None`` is sent as an
      empty value (``param=``) to filter for the null case;
    - for params whose contract only accepts a value (e.g. the timestamp
      filters ``sent_after``/``sent_before``/``ends_from``/``starts_before``/
      ``created_after``), ``None`` keeps the omit-the-param behavior (an empty
      value is not a valid filter for them).
  - a real value         -> param sent with that value

The query-param builder (``utils/values.py::_is_set`` /
``utils/forms.py::_populate_form``) treats ``None`` as "not set" and drops it
unless the field name is listed in ``allow_empty_value``. These tests guard that
wiring against a regeneration that drops it or a manual revert.
"""

import httpx
import pytest

from attio import SDK, errors


# (module attr, sync method, async method, nullable query params, required kwargs)
# Params whose OpenAPI contract documents an empty/null filter; the call site
# passes allow_empty_value=[...] so an explicit None is sent as param=.
EMPTY_VALUE_OPS = [
    ("tasks", "get_v2_tasks", "get_v2_tasks_async", ["assignee"], {}),
]
EMPTY_VALUE_IDS = ["tasks"]

# Nullable GET query params whose contract only accepts a value (timestamps);
# None must keep the omit-the-param behavior (allow_empty_value is not wired).
TIMESTAMP_FILTER_OPS = [
    (
        "emails",
        "get_v2_emails",
        "get_v2_emails_async",
        ["sent_after", "sent_before"],
        {},
    ),
    (
        "meetings",
        "get_v2_meetings",
        "get_v2_meetings_async",
        ["ends_from", "starts_before"],
        {},
    ),
    (
        "threads",
        "get_v2_threads_thread_id_",
        "get_v2_threads_thread_id__async",
        ["created_after"],
        {"thread_id": "th_1"},
    ),
]
TIMESTAMP_FILTER_IDS = ["emails", "meetings", "threads_thread_id"]

ALL_OPS = EMPTY_VALUE_OPS + TIMESTAMP_FILTER_OPS
ALL_IDS = EMPTY_VALUE_IDS + TIMESTAMP_FILTER_IDS


def _build_sdk(captured: dict) -> SDK:
    """Build an SDK whose httpx clients record the outgoing request via a mock
    transport and always return a 200 with empty data. Tests assert only on
    the captured request (the query-param bug), so response-unmarshal failures
    are tolerated by the caller.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json={"data": []})

    transport = httpx.MockTransport(handler)
    return SDK(
        oauth2="test-token",
        client=httpx.Client(transport=transport, follow_redirects=True),
        async_client=httpx.AsyncClient(transport=transport, follow_redirects=True),
    )


def _call(fn, **kwargs):
    try:
        return fn(**kwargs)
    except errors.ResponseValidationError:
        return None


async def _call_async(fn, **kwargs):
    try:
        return await fn(**kwargs)
    except errors.ResponseValidationError:
        return None


@pytest.mark.parametrize(
    "attr,sync_fn,_async_fn,nullable,required", EMPTY_VALUE_OPS, ids=EMPTY_VALUE_IDS
)
def test_sync_explicit_none_sent_empty(attr, sync_fn, _async_fn, nullable, required):
    """An explicit ``None`` reaches the wire as an empty value (``param=``)."""
    captured: dict = {}
    with _build_sdk(captured) as sdk:
        _call(getattr(getattr(sdk, attr), sync_fn), **{p: None for p in nullable}, **required)
    for p in nullable:
        assert captured["params"].get(p) == "", (p, captured["params"])


@pytest.mark.parametrize(
    "attr,sync_fn,_async_fn,nullable,required", TIMESTAMP_FILTER_OPS, ids=TIMESTAMP_FILTER_IDS
)
def test_sync_explicit_none_omits_timestamp_filter(
    attr, sync_fn, _async_fn, nullable, required
):
    """For timestamp filters (no empty-value contract), an explicit ``None`` is
    omitted just like ``UNSET`` -- an empty value is not a valid filter."""
    captured: dict = {}
    with _build_sdk(captured) as sdk:
        _call(getattr(getattr(sdk, attr), sync_fn), **{p: None for p in nullable}, **required)
    for p in nullable:
        assert p not in captured["params"], (p, captured["params"])


@pytest.mark.parametrize(
    "attr,sync_fn,_async_fn,nullable,required", ALL_OPS, ids=ALL_IDS
)
def test_sync_unset_omits_param(attr, sync_fn, _async_fn, nullable, required):
    """Omitting a nullable param (default ``UNSET``) keeps it off the wire."""
    captured: dict = {}
    with _build_sdk(captured) as sdk:
        _call(getattr(getattr(sdk, attr), sync_fn), **required)
    for p in nullable:
        assert p not in captured["params"], (p, captured["params"])


@pytest.mark.parametrize(
    "attr,sync_fn,_async_fn,nullable,required", ALL_OPS, ids=ALL_IDS
)
def test_sync_real_value_sent(attr, sync_fn, _async_fn, nullable, required):
    """A real value is sent unchanged."""
    field = nullable[0]
    captured: dict = {}
    with _build_sdk(captured) as sdk:
        _call(getattr(getattr(sdk, attr), sync_fn), **{field: "abc-123"}, **required)
    assert captured["params"].get(field) == "abc-123", captured["params"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "attr,_sync_fn,async_fn,nullable,required", EMPTY_VALUE_OPS, ids=EMPTY_VALUE_IDS
)
async def test_async_explicit_none_sent_empty(
    attr, _sync_fn, async_fn, nullable, required
):
    """Async variants carry the same wiring as sync."""
    captured: dict = {}
    with _build_sdk(captured) as sdk:
        await _call_async(
            getattr(getattr(sdk, attr), async_fn),
            **{p: None for p in nullable},
            **required,
        )
    for p in nullable:
        assert captured["params"].get(p) == "", (p, captured["params"])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "attr,_sync_fn,async_fn,nullable,required", TIMESTAMP_FILTER_OPS, ids=TIMESTAMP_FILTER_IDS
)
async def test_async_explicit_none_omits_timestamp_filter(
    attr, _sync_fn, async_fn, nullable, required
):
    """For timestamp filters, an explicit ``None`` is omitted on the async path
    too -- an empty value is not a valid filter."""
    captured: dict = {}
    with _build_sdk(captured) as sdk:
        await _call_async(
            getattr(getattr(sdk, attr), async_fn),
            **{p: None for p in nullable},
            **required,
        )
    for p in nullable:
        assert p not in captured["params"], (p, captured["params"])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "attr,_sync_fn,async_fn,nullable,required", ALL_OPS, ids=ALL_IDS
)
async def test_async_unset_omits_param(attr, _sync_fn, async_fn, nullable, required):
    captured: dict = {}
    with _build_sdk(captured) as sdk:
        await _call_async(getattr(getattr(sdk, attr), async_fn), **required)
    for p in nullable:
        assert p not in captured["params"], (p, captured["params"])


def test_two_state_none_siblings_still_omitted_tasks():
    """Two-state ``Optional[X] = None`` fields must still be omitted when
    passed ``None``; only the nullable (three-state) field is sent empty."""
    captured: dict = {}
    with _build_sdk(captured) as sdk:
        _call(
            sdk.tasks.get_v2_tasks,
            assignee=None,
            limit=None,
            offset=None,
            linked_object=None,
        )
    assert captured["params"].get("assignee") == ""
    for two_state in ("limit", "offset", "linked_object"):
        assert two_state not in captured["params"], (two_state, captured["params"])


def test_get_v2_threads_list_unaffected_by_nullable_changes():
    """``get_v2_threads`` (list) has no nullable query params and was not
    patched; passing ``None`` for its two-state fields must still omit them."""
    captured: dict = {}
    with _build_sdk(captured) as sdk:
        _call(sdk.threads.get_v2_threads, record_id=None, limit=None, offset=None)
    for two_state in ("record_id", "limit", "offset"):
        assert two_state not in captured["params"], (two_state, captured["params"])
