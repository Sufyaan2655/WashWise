import { apiFetch } from '../api.js';
import { authStore } from './auth.svelte.js';

function formatDate(value) {
	return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}
function formatTime(value) {
	return new Date(value).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}
function formatStatus(status) {
	return (status || 'confirmed').replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function present(booking) {
	const isWasher = booking.machine_type === 'washer';
	return {
		id: booking.booking_id,
		machine: `${isWasher ? 'Washer' : 'Dryer'} ${booking.machine_number}`,
		date: formatDate(booking.start_time),
		time: formatTime(booking.start_time),
		endTime: formatTime(booking.end_time),
		price: Number(booking.price_at_booking).toFixed(2),
		status: formatStatus(booking.booking_status)
	};
}

class BookingsStore {
	items = $state([]);
	loading = $state(false);

	async load() {
		if (!authStore.user) return;
		this.loading = true;
		try {
			const data = await apiFetch(`/users/${authStore.user.user_id}/bookings`);
			this.items = data.map(present);
		} finally {
			this.loading = false;
		}
	}

	async create({ machineId, price, startTime, endTime }) {
		const result = await apiFetch('/bookings', {
			method: 'POST',
			body: JSON.stringify({
				user_id: authStore.user.user_id,
				machine_id: machineId,
				start_time: startTime,
				end_time: endTime,
				price_at_booking: price
			})
		});
		if (result.booking_id) {
			await apiFetch('/booking-payments', {
				method: 'POST',
				body: JSON.stringify({ booking_id: result.booking_id, gross_amount: price })
			}).catch(() => {});
		}
		return result;
	}

	async cancel(booking) {
		await apiFetch(`/bookings/${booking.id}`, { method: 'DELETE' });
		await this.load();
	}
}

export const bookingsStore = new BookingsStore();
