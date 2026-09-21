import { authStore } from './stores/auth.svelte.js';
import { API_URL } from './config.js';

export class ApiError extends Error {}

/**
 * Fetch wrapper for the WashWise API: prefixes API_URL, attaches the
 * signed-in user's JWT, parses JSON, and normalizes errors.
 */
export async function apiFetch(path, opts = {}) {
	const headers = { ...(opts.headers || {}) };
	if (opts.body) headers['Content-Type'] = 'application/json';
	if (authStore.token) headers['Authorization'] = `Bearer ${authStore.token}`;

	const response = await fetch(`${API_URL}${path}`, { ...opts, headers });

	if (response.status === 401) authStore.logout();

	const isJson = response.headers.get('content-type')?.includes('application/json');
	const data = isJson ? await response.json().catch(() => null) : null;

	if (!response.ok) {
		throw new ApiError(data?.error || `Request to ${path} failed (${response.status}).`);
	}

	return data;
}

export async function apiDownload(path, filename) {
	const headers = {};
	if (authStore.token) headers['Authorization'] = `Bearer ${authStore.token}`;
	const response = await fetch(`${API_URL}${path}`, { headers });
	if (!response.ok) throw new ApiError('Could not download that report.');
	const blob = await response.blob();
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = url;
	link.download = filename;
	link.click();
	URL.revokeObjectURL(url);
}
