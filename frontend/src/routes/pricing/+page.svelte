<script>
	import { fade } from 'svelte/transition';
	import { onMount } from 'svelte';
	import { authStore } from '$lib/stores/auth.svelte.js';
	import { authModalStore } from '$lib/stores/authModal.svelte.js';
	import { noticeStore } from '$lib/stores/notice.svelte.js';
	import { apiFetch } from '$lib/api.js';
	import { goto } from '$app/navigation';

	let pricingAudience = $state('landlord');
	let plans = $state([]);
	let loading = $state(false);

	onMount(async () => {
		try {
			plans = await apiFetch('/plans');
		} catch {
			// pricing still renders without live plans
		}
	});

	async function subscribe(plan) {
		if (!authStore.isLoggedIn || !authStore.isManager) {
			authModalStore.open('signin', 'manager');
			return;
		}
		if (!plan) {
			noticeStore.show('That plan is not available right now.');
			return;
		}
		loading = true;
		try {
			const today = new Date().toISOString().slice(0, 10);
			await apiFetch('/subscriptions', {
				method: 'POST',
				body: JSON.stringify({ building_id: authStore.user.building_id, plan_id: plan.plan_id, start_date: today })
			});
			await goto('/dashboard');
			noticeStore.show(`Your building is now subscribed to ${plan.plan_name}.`);
		} catch (error) {
			noticeStore.show(error.message);
		} finally {
			loading = false;
		}
	}
</script>

<section class="page pricing-page" in:fade={{ duration: 220 }}>
	<div class="wrap">
		<div class="section-intro centered">
			<p class="kicker">One service, two experiences</p>
			<h1>Built for better laundry days.</h1>
			<p>WASHWISE gives property teams control behind the scenes and residents an easy way to get laundry done.</p>
		</div>
		<div class="audience-toggle">
			<button class:chosen={pricingAudience === 'landlord'} onclick={() => (pricingAudience = 'landlord')}>For properties</button>
			<button class:chosen={pricingAudience === 'resident'} onclick={() => (pricingAudience = 'resident')}>For residents</button>
		</div>

		{#if pricingAudience === 'landlord'}
			<div class="pricing-grid">
				<article class="price-card">
					<p class="plan-label">Starter</p>
					<h2>Small buildings,<br />big relief.</h2>
					<div class="price"><b>$79</b><span>/ month</span></div>
					<p class="price-copy">For properties with up to 25 machines.</p>
					<ul>
						<li>Resident booking portal</li>
						<li>Machine status overview</li>
						<li>Flexible per-machine pricing</li>
						<li>Monthly revenue summary</li>
					</ul>
					<button class="button full-width" disabled={loading} onclick={() => subscribe(plans[0])}>
						{authStore.isLoggedIn && authStore.isManager ? `Subscribe to ${plans[0]?.plan_name ?? 'Basic'}` : 'Property team sign in'}
					</button>
				</article>
				<article class="price-card featured">
					<span class="popular">Most popular</span>
					<p class="plan-label">Growth</p>
					<h2>Made for a<br />fuller building.</h2>
					<div class="price"><b>$149</b><span>/ month</span></div>
					<p class="price-copy">For communities with up to 75 machines.</p>
					<ul>
						<li>Everything in Starter</li>
						<li>Performance analytics</li>
						<li>Automated resident reminders</li>
						<li>Priority support</li>
					</ul>
					<button class="button full-width" onclick={() => (window.location.href = 'mailto:sales@washwiseapp.com?subject=Growth Plan Inquiry')}>
						{authStore.isLoggedIn && authStore.isManager ? `Subscribe to ${plans[1]?.plan_name ?? 'Pro'}` : 'Talk to us'} <span>→</span>
					</button>
				</article>
				<article class="price-card">
					<p class="plan-label">Portfolio</p>
					<h2>For every<br />building you run.</h2>
					<div class="price"><b>Let's talk</b></div>
					<p class="price-copy">Custom rollout for multi-property teams.</p>
					<ul>
						<li>Everything in Growth</li>
						<li>Multi-building management</li>
						<li>Custom reporting</li>
						<li>Dedicated onboarding</li>
					</ul>
					<button class="outline-button full-width" onclick={() => (window.location.href = 'mailto:sales@washwiseapp.com?subject=Portfolio Plan Inquiry')}>
						{authStore.isLoggedIn && authStore.isManager ? `Subscribe to ${plans[2]?.plan_name ?? 'Enterprise'}` : 'Contact sales'}
					</button>
				</article>
			</div>
			<p class="pricing-note">All plans include secure resident payments. Machine cycle prices are set by your property team.</p>
		{:else}
			<div class="resident-price">
				<div>
					<p class="plan-label">For residents</p>
					<h2>Your building sets the price. We make it simple.</h2>
					<p>There's no WASHWISE subscription for residents. Create a free account, select your building, and pay only for the washer or dryer cycle you reserve.</p>
					<button class="button" onclick={() => authModalStore.open('signup', 'resident')}>Create free account <span>→</span></button>
				</div>
				<div class="resident-receipt">
					<p>Example booking</p>
					<div><span>Washer 04 · 35 min</span><b>$2.50</b></div>
					<div><span>Service fee</span><b>$0.00</b></div>
					<hr />
					<div class="total"><span>Total today</span><b>$2.50</b></div>
					<small>Cycle prices vary by building and are set by its property team.</small>
				</div>
			</div>
		{/if}
	</div>
</section>
