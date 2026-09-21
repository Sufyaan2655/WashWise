<script>
	import { fade } from 'svelte/transition';
	import { onMount } from 'svelte';
	import { authStore } from '$lib/stores/auth.svelte.js';
	import { authModalStore } from '$lib/stores/authModal.svelte.js';
	import { noticeStore } from '$lib/stores/notice.svelte.js';
	import { machinesStore } from '$lib/stores/machines.svelte.js';
	import { bookingsStore } from '$lib/stores/bookings.svelte.js';
	import { waitlistStore } from '$lib/stores/waitlist.svelte.js';
	import MachineCard from '$lib/components/MachineCard.svelte';
	import ReservationModal from '$lib/components/ReservationModal.svelte';

	let machineFilter = $state('all');
	let selectedMachine = $state(null);
	let reserveLoading = $state(false);
	let reserveError = $state('');

	const filtered = $derived(
		machinesStore.items.filter((m) => machineFilter === 'all' || m.type.toLowerCase() === machineFilter)
	);

	onMount(() => {
		machinesStore.load();
		if (authStore.isLoggedIn) waitlistStore.load();
	});

	function reserve(machine) {
		if (!authStore.isLoggedIn) {
			noticeStore.show('Sign in as a resident to reserve a machine.');
			authModalStore.open('signin', 'resident');
			return;
		}
		if (authStore.isManager) {
			noticeStore.show('Manager accounts can view machine status but cannot make resident reservations.');
			return;
		}
		selectedMachine = machine;
		reserveError = '';
	}

	function closeReservation() {
		selectedMachine = null;
		reserveError = '';
	}

	function createDateTime(date, time) {
		const [part, period] = time.split(' ');
		let [hours, minutes] = part.split(':').map(Number);
		if (period === 'PM' && hours !== 12) hours += 12;
		if (period === 'AM' && hours === 12) hours = 0;
		const result = new Date(`${date}T00:00:00`);
		result.setHours(hours, minutes, 0, 0);
		return result;
	}
	function formatForBackend(date) {
		return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:00`;
	}

	async function confirmReservation(selectedDate, selectedTime) {
		if (!selectedDate || !selectedTime) {
			reserveError = 'Choose a date and a time first.';
			return;
		}
		reserveLoading = true;
		reserveError = '';
		try {
			const startDate = createDateTime(selectedDate, selectedTime);
			const endDate = new Date(startDate.getTime() + selectedMachine.duration * 60000);
			await bookingsStore.create({
				machineId: selectedMachine.id,
				price: selectedMachine.price,
				startTime: formatForBackend(startDate),
				endTime: formatForBackend(endDate)
			});
			closeReservation();
			await bookingsStore.load();
			await machinesStore.load();
			noticeStore.show('Your laundry time is confirmed and paid.');
		} catch (error) {
			reserveError = error.message;
		} finally {
			reserveLoading = false;
		}
	}

	async function joinWaitlist(machine) {
		if (!authStore.isLoggedIn) {
			authModalStore.open('signin', 'resident');
			return;
		}
		await waitlistStore.join(machine.id);
		noticeStore.show(`You're on the waitlist for ${machine.name}. We'll notify you when it's free.`);
	}
</script>

<section class="page wrap" in:fade={{ duration: 220 }}>
	<div class="section-intro">
		<p class="kicker">{authStore.isLoggedIn ? `Your building` : 'Live machine status'}</p>
		<h1>Find your next machine.</h1>
		<p>Availability updates as cycles start and end.</p>
	</div>
	<div class="toolbar">
		<div class="filter-pills">
			<button class:selected={machineFilter === 'all'} onclick={() => (machineFilter = 'all')}>All machines</button>
			<button class:selected={machineFilter === 'washer'} onclick={() => (machineFilter = 'washer')}>Washers</button>
			<button class:selected={machineFilter === 'dryer'} onclick={() => (machineFilter = 'dryer')}>Dryers</button>
		</div>
		<button class="icon-button" onclick={() => machinesStore.load()} aria-label="Refresh availability">↻ Refresh</button>
	</div>
	<div class="machine-grid">
		{#each filtered as machine (machine.id)}
			<MachineCard {machine} onReserve={reserve} onJoinWaitlist={authStore.isLoggedIn && !authStore.isManager ? joinWaitlist : null} />
		{/each}
	</div>
</section>

{#if selectedMachine}
	<ReservationModal
		machine={selectedMachine}
		loading={reserveLoading}
		error={reserveError}
		onConfirm={confirmReservation}
		onClose={closeReservation}
	/>
{/if}
