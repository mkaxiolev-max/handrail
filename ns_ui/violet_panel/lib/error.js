// Error state helpers — shows RED on fetch fail

export function isError(data) {
  if (!data) return true;
  if (data._error) return true;
  if (data.return_block_version === 2 && data.ok === false) return true;
  return false;
}

export function errorMessage(data) {
  if (!data) return 'No data';
  if (data._error) return `Disconnected (${data.status || 0}): ${data.detail || ''}`;
  if (data.failure_reason) return data.failure_reason;
  return 'Unknown error';
}
