import { API_URL } from '../config.js';

const STORAGE_KEY = 'washwise.auth';

function loadStored() {
	if (typeof localStorage === 'undefined') return { token: null, user: null };
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		return raw ? JSON.parse(raw) : { token: null, user: null };
	} catch {
		return { token: null, user: null };
	}
}

const stored = loadStored();

class AuthStore {
	token = $state(stored.token);
	user = $state(stored.user);
	restoring = $state(false);

	get isLoggedIn() {
		return Boolean(this.user);
	}

	get isManager() {
		return this.user?.role === 'manager';
	}

	_persist() {
		if (typeof localStorage === 'undefined') return;
		if (this.token && this.user) {
			localStorage.setItem(STORAGE_KEY, JSON.stringify({ token: this.token, user: this.user }));
		} else {
			localStorage.removeItem(STORAGE_KEY);
		}
	}

	async login(email, password) {
		const response = await fetch(`${API_URL}/login`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, password })
		});
		const data = await response.json();
		if (!response.ok) throw new Error(data.error || 'We could not sign you in.');

		this.token = data.token;
		this.user = {
			user_id: data.user_id,
			building_id: data.building_id,
			name: data.name,
			email: data.email,
			role: data.role
		};
		this._persist();
		return this.user;
	}

	logout() {
		this.token = null;
		this.user = null;
		this._persist();
	}

	/** Re-validate the stored token against the API on app load. */
	async restore() {
		if (!this.token) return;
		this.restoring = true;
		try {
			const response = await fetch(`${API_URL}/me`, {
				headers: { Authorization: `Bearer ${this.token}` }
			});
			if (!response.ok) {
				this.logout();
				return;
			}
			this.user = await response.json();
			this._persist();
		} catch {
			// offline / API unreachable — keep the cached session, next call will re-check
		} finally {
			this.restoring = false;
		}
	}
}

export const authStore = new AuthStore();
