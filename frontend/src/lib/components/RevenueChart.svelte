<script>
	// Stacked daily revenue (booking fees + subscription fees), one y-axis.
	// Palette: validated categorical slots 1 (blue) + 2 (orange) — see dataviz skill.
	let { rows } = $props();

	const BOOKING_COLOR = '#2a78d6';
	const SUBSCRIPTION_COLOR = '#eb6834';

	let showTable = $state(false);

	const totals = $derived(rows.map((r) => r.booking_revenue + r.subscription_revenue));
	const max = $derived(Math.max(1, ...totals));

	const width = 640;
	const height = 200;
	const padding = { top: 10, right: 10, bottom: 26, left: 10 };
	const plotW = width - padding.left - padding.right;
	const plotH = height - padding.top - padding.bottom;

	const barGap = 4;
	const barWidth = $derived(rows.length ? Math.max(4, plotW / rows.length - barGap) : 0);

	function x(i) {
		return padding.left + i * (plotW / Math.max(1, rows.length));
	}
	function barHeight(value) {
		return max === 0 ? 0 : (value / max) * plotH;
	}
	function shortDate(day) {
		return new Date(`${day}T00:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}
</script>

<div class="chart-wrap">
	{#if rows.length === 0}
		<p class="notif-empty">No revenue recorded in this window yet.</p>
	{:else}
		<div class="chart-legend">
			<span><i style="background: {BOOKING_COLOR}"></i>Booking fees</span>
			<span><i style="background: {SUBSCRIPTION_COLOR}"></i>Subscription</span>
			<button class="text-button" onclick={() => (showTable = !showTable)}>
				{showTable ? 'View chart' : 'View as table'}
			</button>
		</div>

		{#if showTable}
			<table class="chart-table">
				<thead><tr><th>Day</th><th>Booking fees</th><th>Subscription</th><th>Total</th></tr></thead>
				<tbody>
					{#each rows as row}
						<tr>
							<td>{shortDate(row.day)}</td>
							<td>${row.booking_revenue.toFixed(2)}</td>
							<td>${row.subscription_revenue.toFixed(2)}</td>
							<td>${(row.booking_revenue + row.subscription_revenue).toFixed(2)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{:else}
			<svg viewBox="0 0 {width} {height}" role="img" aria-label="Daily revenue, booking fees and subscription fees stacked, last {rows.length} days">
				{#each rows as row, i}
					{@const bookingH = barHeight(row.booking_revenue)}
					{@const subH = barHeight(row.subscription_revenue)}
					{@const barX = x(i)}
					{@const baseY = padding.top + plotH}
					<g>
						<title>{shortDate(row.day)}: ${row.booking_revenue.toFixed(2)} booking + ${row.subscription_revenue.toFixed(2)} subscription = ${(row.booking_revenue + row.subscription_revenue).toFixed(2)}</title>
						{#if subH > 0}
							<rect x={barX} y={baseY - subH} width={barWidth} height={subH} rx="2" fill={SUBSCRIPTION_COLOR} />
						{/if}
						{#if bookingH > 0}
							<rect x={barX} y={baseY - subH - bookingH - (subH > 0 ? 2 : 0)} width={barWidth} height={bookingH} rx="2" fill={BOOKING_COLOR} />
						{/if}
					</g>
					{#if i === 0 || i === rows.length - 1 || i === Math.floor(rows.length / 2)}
						<text x={barX + barWidth / 2} y={height - 8} text-anchor="middle" font-size="10" fill="#8a958f">{shortDate(row.day)}</text>
					{/if}
				{/each}
			</svg>
		{/if}
	{/if}
</div>

<style>
	.chart-wrap { margin-top: 16px; }
	.chart-legend { display: flex; align-items: center; gap: 16px; margin-bottom: 10px; font-size: 12px; color: #5c7065; }
	.chart-legend span { display: inline-flex; align-items: center; gap: 6px; }
	.chart-legend i { display: inline-block; width: 9px; height: 9px; border-radius: 2px; }
	.chart-legend .text-button { margin-left: auto; padding: 4px 0; }
	svg { width: 100%; height: auto; }
	.chart-table { width: 100%; border-collapse: collapse; font-size: 12px; }
	.chart-table th, .chart-table td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #e2e5de; color: #3a463f; }
	.chart-table th { color: #738178; font-weight: 700; }
</style>
