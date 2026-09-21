<script>
	import { fade } from 'svelte/transition';
	import { onMount } from 'svelte';
	import { authStore } from '$lib/stores/auth.svelte.js';
	import { authModalStore } from '$lib/stores/authModal.svelte.js';
	import { noticeStore } from '$lib/stores/notice.svelte.js';
	import { bookingsStore } from '$lib/stores/bookings.svelte.js';
	import { waitlistStore } from '$lib/stores/waitlist.svelte.js';
	import { goto } from '$app/navigation';
	import BookingCard from '$lib/components/BookingCard.svelte';

	onMount(() => {
		if (authStore.isLoggedIn) {
			bookingsStore.load();
			waitlistStore.load();
		}
	});

	async function cancelBooking(booking) {
		if (!confirm(`Cancel ${booking.machine} on ${booking.date}?`)) return;
		try {
			await bookingsStore.cancel(booking);
			noticeStore.show('Reservation cancelled.');
		} catch (error) {
			noticeStore.show(error.message);
		}
	}

	async function leaveWaitlist(entry) {
		await waitlistStore.leave(entry.waitlist_id);
		noticeStore.show('Removed from the waitlist.');
	}
</script>

<section class="page wrap" in:fade={{ duration: 220 }}>
	<div class="section-intro">
		<p class="kicker">Resident account</p>
		<h1>Your laundry schedule.</h1>
		<p>Everything you have booked, all in one place.</p>
	</div>

	{#if !authStore.isLoggedIn}
		<div class="empty-state">
			<div class="empty-icon">◉</div>
			<h2>Your next wash is waiting.</h2>
			<p>Sign in to view, manage, and reserve your building's machines.</p>
			<button class="button" onclick={() => authModalStore.open('signin', 'resident')}>Sign in as resident</button>
		</div>
	{:else if bookingsStore.items.length === 0 && !bookingsStore.loading}
		<div class="empty-state">
			<div class="empty-icon">◎</div>
			<h2>Nothing booked yet.</h2>
			<p>Choose an available machine and make the time yours.</p>
			<button class="button" onclick={() => goto('/machines')}>Find a machine</button>
		</div>
	{:else}
		<div class="booking-list">
			{#each bookingsStore.items as booking (booking.id)}
				<BookingCard {booking} onCancel={cancelBooking} />
			{/each}
		</div>
	{/if}

	{#if authStore.isLoggedIn && waitlistStore.items.some((w) => w.status === 'waiting')}
		<div class="section-intro" style="margin-top: 60px;">
			<p class="kicker">Waitlist</p>
			<h2>Machines you're waiting on.</h2>
		</div>
		<div class="booking-list">
			{#each waitlistStore.items.filter((w) => w.status === 'waiting') as entry (entry.waitlist_id)}
				<article class="booking-card">
					<div class="booking-main">
						<span class="confirmed">Waiting</span>
						<h2>{entry.machine_type === 'washer' ? 'Washer' : 'Dryer'} {entry.machine_number}</h2>
						<p>Joined {new Date(entry.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</p>
					</div>
					<div></div>
					<button class="cancel-button" onclick={() => leaveWaitlist(entry)}>Leave waitlist</button>
				</article>
			{/each}
		</div>
	{/if}
</section>
