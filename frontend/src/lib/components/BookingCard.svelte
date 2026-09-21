<script>
	import { fly } from 'svelte/transition';

	let { booking, onCancel } = $props();
	const isFinal = $derived(booking.status === 'Cancelled' || booking.status === 'Completed');
</script>

<article class="booking-card" transition:fly={{ y: 12, duration: 180 }}>
	<div class="booking-main">
		<span class="confirmed">{booking.status}</span>
		<h2>{booking.machine}</h2>
		<p>{booking.date} · {booking.time}–{booking.endTime}</p>
	</div>
	<div class="booking-price"><span>Paid</span><b>${booking.price}</b></div>
	{#if !isFinal}<button class="cancel-button" onclick={() => onCancel(booking)}>Cancel</button>{/if}
</article>
