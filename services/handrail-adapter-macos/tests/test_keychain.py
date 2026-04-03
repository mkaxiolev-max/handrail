"""
Tests for keychain.* namespace handlers.
All subprocess calls are monkeypatched — no real keychain access.
Dignity Guard: never returns secret values, blocks shell metacharacters.
"""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from keychain_driver.handlers import (
    keychain_check_entry,
    keychain_list_services,
    build_keychain_handlers,
)


def _req(method: str, **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)


# ── keychain.check_entry ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_check_entry_exists():
    with patch("keychain_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "", "")   # rc=0 → exists
        resp = await keychain_check_entry(_req("keychain.check_entry", service="MyApp", account="user"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["exists"] is True
    assert resp.data["service"] == "MyApp"
    # Dignity Guard: no password/secret field in response
    assert "value" not in resp.data
    assert "password" not in resp.data


@pytest.mark.asyncio
async def test_check_entry_not_found():
    with patch("keychain_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (44, "", "SecKeychainSearchCopyNext")  # rc=44 → not found
        resp = await keychain_check_entry(_req("keychain.check_entry", service="NoSuchApp", account="user"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["exists"] is False


@pytest.mark.asyncio
async def test_check_entry_permission_error_rc():
    with patch("keychain_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (1, "", "User interaction is not allowed")
        resp = await keychain_check_entry(_req("keychain.check_entry", service="LockedApp", account="u"))

    # Non-zero non-44 → does not exist (safe default)
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["exists"] is False


@pytest.mark.asyncio
async def test_check_entry_missing_service():
    resp = await keychain_check_entry(_req("keychain.check_entry", account="user"))
    assert resp.status == OperationStatus.FAILURE
    assert "params.service required" in resp.error


@pytest.mark.asyncio
async def test_check_entry_dignity_guard_shell_meta_semicolon():
    with pytest.raises(PermissionError, match="shell metacharacters"):
        await keychain_check_entry(_req("keychain.check_entry", service="foo;rm -rf /", account="u"))


@pytest.mark.asyncio
async def test_check_entry_dignity_guard_shell_meta_backtick():
    with pytest.raises(PermissionError, match="shell metacharacters"):
        await keychain_check_entry(_req("keychain.check_entry", service="foo`id`", account="u"))


@pytest.mark.asyncio
async def test_check_entry_dignity_guard_shell_meta_pipe():
    with pytest.raises(PermissionError, match="shell metacharacters"):
        await keychain_check_entry(_req("keychain.check_entry", service="foo|bar", account="u"))


@pytest.mark.asyncio
async def test_check_entry_no_account_param():
    """account is optional — should call security without -a flag."""
    with patch("keychain_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "", "")
        resp = await keychain_check_entry(_req("keychain.check_entry", service="MyApp"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["exists"] is True
    call_args = mock_run.call_args[0][0]
    assert "-a" not in call_args


# ── keychain.list_services ────────────────────────────────────────────────────

_DUMP_OUTPUT = '''
keychain: "/Users/user/Library/Keychains/login.keychain-db"
class: "genp"
attributes:
    "svce" <blob>= "MyWebApp"
    "acct" <blob>= "admin"
keychain: "/Users/user/Library/Keychains/login.keychain-db"
class: "genp"
attributes:
    "svce" <blob>= "GitHubSSH"
    "acct" <blob>= "git"
keychain: "/Users/user/Library/Keychains/login.keychain-db"
class: "genp"
attributes:
    "svce" <blob>= "SecretTokenService"
    "acct" <blob>= "user"
'''


@pytest.mark.asyncio
async def test_list_services_success():
    with patch("keychain_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, _DUMP_OUTPUT, "")
        resp = await keychain_list_services(_req("keychain.list_services"))

    assert resp.status == OperationStatus.SUCCESS
    services = resp.data["services"]
    assert "MyWebApp" in services
    assert "GitHubSSH" in services
    # Dignity Guard: "SecretTokenService" contains "token" — must be filtered
    assert "SecretTokenService" not in services
    assert resp.data["count"] == len(services)


@pytest.mark.asyncio
async def test_list_services_empty_keychain():
    with patch("keychain_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "", "")
        resp = await keychain_list_services(_req("keychain.list_services"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["services"] == []
    assert resp.data["count"] == 0


@pytest.mark.asyncio
async def test_list_services_command_failure():
    with patch("keychain_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (1, "", "security: dump-keychain not allowed")
        resp = await keychain_list_services(_req("keychain.list_services"))

    # Graceful: returns empty list on failure
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["services"] == []


@pytest.mark.asyncio
async def test_list_services_no_secret_values_in_output():
    """Confirm that password-bearing lines are never included."""
    dump_with_secrets = (
        '    "svce" <blob>= "SafeApp"\n'
        '    "svce" <blob>= "MyPasswordManager"\n'   # contains "pass"
        '    "svce" <blob>= "SecretVault"\n'           # contains "secret"
        '    "svce" <blob>= "APIKeyStore"\n'            # contains "key"
        '    "svce" <blob>= "TokenBucket"\n'            # contains "token"
        '    "svce" <blob>= "CleanService"\n'
    )
    with patch("keychain_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, dump_with_secrets, "")
        resp = await keychain_list_services(_req("keychain.list_services"))

    services = resp.data["services"]
    for svc in services:
        assert not any(bad in svc.lower() for bad in ["pass", "pwd", "secret", "token", "key"]), \
            f"Dignity Guard failed: {svc!r} should have been filtered"
    assert "SafeApp" in services
    assert "CleanService" in services


# ── registry ──────────────────────────────────────────────────────────────────

def test_build_keychain_handlers_keys():
    handlers = build_keychain_handlers()
    assert set(handlers.keys()) == {"keychain.check_entry", "keychain.list_services"}
    for fn in handlers.values():
        assert callable(fn)
