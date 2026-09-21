import { apiFetch } from '../api.js';
import { authStore } from './auth.svelte.js';

function present(machine) {
	const isWasher = machine.machine_type === 'washer';
	const statusLabel =
		machine.status === 'active' ? 'Available'
		: machine.status === 'in_use' ? 'In use'
		: machine.status === 'maintenance' ? 'Maintenance'
		: 'Reserved';
	return {
		id: machine.machine_id,
		name: `${isWasher ? 'Washer' : 'Dryer'} ${machine.machine_number}`,
		type: isWasher ? 'Washer' : 'Dryer',
		icon: isWasher ? '◉' : '◌',
		status: statusLabel,
		detail:
			machine.status === 'active' ? `${machine.duration_minutes} min cycle · $${Number(machine.cost_per_cycle).toFixed(2)}`
			: machine.status === 'in_use' ? 'Currently running'
			: machine.status === 'maintenance' ? 'Temporarily offline'
			: 'Held for a resident',
		duration: machine.duration_minutes,
		price: Number(machine.cost_per_cycle)
	};
}

class MachinesStore {
	items = $state([]);
	loading = $state(false);

	get available() {
		return this.items.filter((m) => m.status === 'Available').length;
	}

	async load() {
		this.loading = true;
		try {
			const buildingId = authStore.user?.building_id ?? '';
			const data = await apiFetch(`/machines?building_id=${buildingId}`);
			this.items = data.map(present);
		} finally {
			this.loading = false;
		}
	}

	async setStatus(machine, status) {
		await apiFetch(`/machines/${machine.id}`, {
			method: 'PATCH',
			body: JSON.stringify({ status })
		});
		await this.load();
	}
}

export const machinesStore = new MachinesStore();
