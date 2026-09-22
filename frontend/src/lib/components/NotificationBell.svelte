<script>
	import { fly } from 'svelte/transition';
	import { notificationsStore } from '../stores/notifications.svelte.js';

	let open = $state(false);

	function toggle() {
		open = !open;
		if (open) notificationsStore.load();
	}

	function timeAgo(value) {
		const diffMs = Date.now() - new Date(value).getTime();
		const minutes = Math.round(diffMs / 60000);
		if (minutes < 1) return 'just now';
		if (minutes < 60) return `${minutes}m ago`;
		const hours = Math.round(minutes / 60);
		if (hours < 24) return `${hours}h ago`;
		return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}
</script>

<div style="position: relative;">
	<button class="notif-bell" onclick={toggle} aria-label="Notifications">
		{#if notificationsStore.unreadCount > 0}<span class="notif-dot"></span>{/if}
	</button>

	{#if open}
		<div class="notif-panel" transition:fly={{ y: -8, duration: 160 }}>
			<h3>Notifications</h3>
			{#if notificationsStore.items.length === 0}
				<p class="notif-empty">Nothing yet — you'll see booking and waitlist updates here.</p>
			{:else}
				{#each notificationsStore.items as notification (notification.notification_id)}
					<button
						class="notif-row"
						class:unread={!notification.is_read}
						onclick={() => notificationsStore.markRead(notification)}
					>
						{notification.message}
						<time>{timeAgo(notification.created_at)}</time>
					</button>
				{/each}
			{/if}
		</div>
	{/if}
</div>
