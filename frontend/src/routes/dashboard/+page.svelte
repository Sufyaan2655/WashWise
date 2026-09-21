<script>
	import { fade } from 'svelte/transition';
	import { onMount } from 'svelte';
	import { authStore } from '$lib/stores/auth.svelte.js';
	import { authModalStore } from '$lib/stores/authModal.svelte.js';
	import { noticeStore } from '$lib/stores/notice.svelte.js';
	import { machinesStore } from '$lib/stores/machines.svelte.js';
	import { apiFetch, apiDownload } from '$lib/api.js';
	import { goto } from '$app/navigation';
	import InventoryRow from '$lib/components/InventoryRow.svelte';
	import RevenueChart from '$lib/components/RevenueChart.svelte';

	let revenue = $state(null);
	let subscription = $state(null);
	let timeseries = $state([]);

	async function loadDashboard() {
		await machinesStore.load();
		await Promise.all([loadRevenue(), loadSubscription(), loadTimeseries()]);
	}

	async function loadRevenue() {
		try {
			const data = await apiFetch('/reports/revenue');
			revenue = data.find((row) => Number(row.building_id) === authStore.user.building_id)
				|| { booking_revenue: 0, subscription_revenue: 0 };
		} catch {
			revenue = null;
		}
	}

	async function loadSubscription() {
		try {
			const data = await apiFetch('/subscriptions');
			const mine = data.filter((row) => Number(row.building_id) === authStore.user.building_id);
			subscription = mine.length ? mine[mine.length - 1] : null;
		} catch {
			subscription = null;
		}
	}

	async function loadTimeseries() {
		try {
			timeseries = await apiFetch('/reports/revenue/timeseries?days=30');
		} catch {
			timeseries = [];
		}
	}

	async function toggleMachineStatus(machine) {
		const newStatus = machine.status === 'Maintenance' ? 'active' : 'maintenance';
		try {
			await machinesStore.setStatus(machine, newStatus);
		} catch (error) {
			noticeStore.show(error.message);
		}
	}

	async function downloadReport() {
		try {
			await apiDownload('/reports/revenue/export', 'revenue_report.xlsx');
		} catch (error) {
			noticeStore.show(error.message);
		}
	}

	onMount(() => {
		if (authStore.isLoggedIn && authStore.isManager) loadDashboard();
	});
</script>

<section class="page wrap dashboard" in:fade={{ duration: 220 }}>
	{#if !authStore.isLoggedIn || !authStore.isManager}
		<div class="empty-state">
			<div class="empty-icon">▦</div>
			<h2>Property team access only.</h2>
			<p>Sign in with your developer or admin account to manage your building.</p>
			<button class="button" onclick={() => authModalStore.open('signin', 'manager')}>Property team sign in</button>
		</div>
	{:else}
		<div class="dashboard-heading">
			<div>
				<p class="kicker">Property workspace</p>
				<h1>Good morning, {authStore.user.name}.</h1>
				<p>Here's what is happening in your laundry room today.</p>
			</div>
			<button class="icon-button" onclick={loadDashboard}>↻ Refresh data</button>
		</div>

		<div class="metric-grid">
			<article>
				<span>Available now</span>
				<b>{machinesStore.available}<small> / {machinesStore.items.length} machines</small></b>
				<p class="positive">● Healthy availability</p>
			</article>
			<article>
				<span>Maintenance</span>
				<b>{machinesStore.items.filter((m) => m.status === 'Maintenance').length}</b>
				<p>Machines requiring attention</p>
			</article>
			<article>
				<span>Booking fees</span>
				<b>${Number(revenue?.booking_revenue || 0).toFixed(2)}</b>
				<p>Platform revenue to date</p>
			</article>
			<article>
				<span>Current plan</span>
				<b class="plan-value">{subscription?.plan_name || 'Starter'}</b>
				<p>{subscription?.billing_period || 'Monthly billing'}</p>
			</article>
		</div>

		<div class="dashboard-panels">
			<article class="panel inventory">
				<div class="panel-heading">
					<div><p class="plan-label">Machine control</p><h2>Machine inventory</h2></div>
					<button class="text-button" onclick={() => goto('/machines')}>Open resident view →</button>
				</div>
				{#each machinesStore.items as machine (machine.id)}
					<InventoryRow {machine} onToggle={toggleMachineStatus} />
				{/each}
			</article>
			<article class="panel revenue">
				<p class="plan-label">Revenue</p>
				<h2>At a glance</h2>
				<div class="revenue-number">${(Number(revenue?.booking_revenue || 0) + Number(revenue?.subscription_revenue || 0)).toFixed(2)}</div>
				<p>Total platform revenue recorded for this building.</p>
				<button class="outline-button full-width" onclick={downloadReport}>Download revenue report</button>
			</article>
			<article class="panel chart-panel">
				<p class="plan-label">Trend</p>
				<h2>Revenue, last 30 days</h2>
				<RevenueChart rows={timeseries} />
			</article>
		</div>
	{/if}
</section>
