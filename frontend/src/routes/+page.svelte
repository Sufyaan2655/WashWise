<script>
	import { fade } from 'svelte/transition';
	import { goto } from '$app/navigation';
	import { authModalStore } from '$lib/stores/authModal.svelte.js';
	import { machinesStore } from '$lib/stores/machines.svelte.js';
</script>

<div class="page" in:fade={{ duration: 260 }}>
	<section class="hero wrap">
		<div class="hero-copy">
			<p class="kicker">Laundry, without the waiting</p>
			<h1>One less thing<br />to plan around.</h1>
			<p class="lead">See what's open, book a time that works, and pay before you head downstairs.</p>
			<div class="hero-actions">
				<button class="button" onclick={() => goto('/machines')}>Check availability <span>→</span></button>
				<button class="link-button" onclick={() => authModalStore.open('signup', 'resident')}>Create resident account</button>
			</div>
			<div class="trust-line"><span>●</span> Live availability from your building</div>
		</div>
		<div class="hero-visual" aria-label="Laundry booking preview">
			<div class="glow"></div>
			<div class="visual-top"><span>Good afternoon, Maya</span><span class="avatar">M</span></div>
			<div class="visual-title">Your next wash</div>
			<div class="reservation-preview">
				<div class="machine-dot washer">◉</div>
				<div><strong>Washer 04</strong><span>Today · 6:30–7:05 PM</span></div>
				<b>$2.50</b>
			</div>
			<div class="availability-row"><span>Available now</span><b>{machinesStore.available} machines</b></div>
			<div class="mini-machines">
				{#each machinesStore.items.slice(0, 4) as machine}
					<div class:open={machine.status === 'Available'}><i>{machine.icon}</i><span>{machine.name.slice(-2)}</span></div>
				{/each}
			</div>
		</div>
	</section>

	<section class="benefits wrap">
		<div><p class="kicker">A calmer laundry room</p><h2>Built around real life.</h2></div>
		<div class="benefit-list">
			<article><span>01</span><h3>Know before you go</h3><p>Real-time availability keeps the guessing out of laundry day.</p></article>
			<article><span>02</span><h3>Reserve your window</h3><p>Choose a machine and a time, then get on with your day.</p></article>
			<article><span>03</span><h3>Simple at checkout</h3><p>Pay securely when you book—no coins, no scrambling.</p></article>
		</div>
	</section>

	<section class="property-banner wrap">
		<div><p class="kicker">For property teams</p><h2>Better operations start<br />with better visibility.</h2></div>
		<div>
			<p>Give residents a thoughtful amenity while your team manages machines, pricing, and performance in one place.</p>
			<button class="button light" onclick={() => goto('/pricing')}>Explore WASHWISE for properties <span>→</span></button>
		</div>
	</section>
</div>
