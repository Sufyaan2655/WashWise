<script>
	import { scale } from 'svelte/transition';
	import { waitlistStore } from '../stores/waitlist.svelte.js';

	let { machine, onReserve, onJoinWaitlist } = $props();

	const isAvailable = $derived(machine.status === 'Available');
	const isWaiting = $derived(waitlistStore.isWaiting(machine.id));
</script>

<article class="machine-card" transition:scale={{ duration: 180, start: 0.96 }}>
	<div class="machine-card-top">
		<span class="machine-symbol {machine.type.toLowerCase()}">{machine.icon}</span>
		<span class:available={isAvailable} class="status">{machine.status}</span>
	</div>
	<h3>{machine.name}</h3>
	<p>{machine.type} · {machine.detail}</p>
	<button class="card-action" disabled={!isAvailable} onclick={() => onReserve(machine)}>
		{isAvailable ? 'Reserve this machine' : 'Not available'} <span>→</span>
	</button>
	{#if !isAvailable && onJoinWaitlist}
		<button class="waitlist-action" class:joined={isWaiting} disabled={isWaiting} onclick={() => onJoinWaitlist(machine)}>
			{isWaiting ? "You're on the waitlist" : 'Notify me when it\'s free'}
		</button>
	{/if}
</article>
