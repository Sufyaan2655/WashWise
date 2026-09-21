import { apiFetch } from '../api.js';
import { authStore } from './auth.svelte.js';

class NotificationsStore {
	items = $state([]);

	get unreadCount() {
		return this.items.filter((n) => !n.is_read).length;
	}

	async load() {
		if (!authStore.user) return;
		try {
			this.items = await apiFetch(`/users/${authStore.user.user_id}/notifications`);
		} catch {
			// notifications are a nice-to-have; a failed load shouldn't break the page
		}
	}

	async markRead(notification) {
		if (notification.is_read) return;
		notification.is_read = true;
		try {
			await apiFetch(`/notifications/${notification.notification_id}/read`, { method: 'POST' });
		} catch {
			notification.is_read = false;
		}
	}

	clear() {
		this.items = [];
	}
}

export const notificationsStore = new NotificationsStore();
