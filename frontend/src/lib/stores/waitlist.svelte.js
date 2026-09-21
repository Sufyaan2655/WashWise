import { apiFetch } from '../api.js';
import { authStore } from './auth.svelte.js';

class WaitlistStore {
	items = $state([]);

	isWaiting(machineId) {
		return this.items.some((w) => w.machine_id === machineId && w.status === 'waiting');
	}

	async load() {
		if (!authStore.user) return;
		this.items = await apiFetch(`/users/${authStore.user.user_id}/waitlist`);
	}

	async join(machineId) {
		await apiFetch(`/machines/${machineId}/waitlist`, {
			method: 'POST',
			body: JSON.stringify({ user_id: authStore.user.user_id })
		});
		await this.load();
	}

	async leave(waitlistId) {
		await apiFetch(`/waitlist/${waitlistId}`, { method: 'DELETE' });
		await this.load();
	}
}

export const waitlistStore = new WaitlistStore();
