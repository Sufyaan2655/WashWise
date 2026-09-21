<script>
	import { fade, fly } from 'svelte/transition';

	let { machine, loading, error, onConfirm, onClose } = $props();

	let selectedDate = $state('');
	let selectedTime = $state('');

	const times = ['8:00 AM', '9:00 AM', '10:00 AM', '11:00 AM', '12:00 PM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM', '5:00 PM', '6:00 PM', '7:00 PM'];

	function confirm() {
		onConfirm(selectedDate, selectedTime);
	}
</script>

<div class="modal-backdrop" transition:fade={{ duration: 160 }} role="presentation">
	<div class="auth-modal reservation-modal" transition:fly={{ y: 18, duration: 220 }} role="dialog" aria-modal="true">
		<button class="close" onclick={onClose} aria-label="Close">×</button>
		<p class="kicker">Reserve a machine</p>
		<h2>{machine.name}</h2>
		<div class="reservation-summary">
			<span class="machine-symbol {machine.type.toLowerCase()}">{machine.icon}</span>
			<div><b>{machine.duration} minute cycle</b><span>Pay now · guaranteed time</span></div>
			<strong>${machine.price.toFixed(2)}</strong>
		</div>
		<div class="form-grid">
			<label>Date<input type="date" bind:value={selectedDate} /></label>
			<label>Start time
				<select bind:value={selectedTime}>
					<option value="">Select a time</option>
					{#each times as time}<option>{time}</option>{/each}
				</select>
			</label>
		</div>
		<button class="button full-width" onclick={confirm} disabled={loading}>
			{loading ? 'Confirming…' : `Pay $${machine.price.toFixed(2)} & reserve`} <span>→</span>
		</button>
		{#if error}<p class="form-message">{error}</p>{/if}
	</div>
</div>
