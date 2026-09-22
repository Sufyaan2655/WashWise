<script>
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { authStore } from '../stores/auth.svelte.js';
	import { authModalStore } from '../stores/authModal.svelte.js';
	import { noticeStore } from '../stores/notice.svelte.js';
	import { bookingsStore } from '../stores/bookings.svelte.js';
	import { notificationsStore } from '../stores/notifications.svelte.js';
	import { themeStore } from '../stores/theme.svelte.js';
	import NotificationBell from './NotificationBell.svelte';

	function isActive(path) {
		return page.url.pathname === path;
	}

	function logout() {
		authStore.logout();
		bookingsStore.items = [];
		notificationsStore.clear();
		noticeStore.show('You have been signed out.');
		goto('/');
	}
</script>

<header>
	<a class="brand" href="/" aria-label="WASHWISE home"><span class="brand-mark">W</span> WASHWISE</a>
	<nav aria-label="Main navigation">
		<a class:active={isActive('/machines')} href="/machines">Find a machine</a>
		<a class:active={isActive('/pricing')} href="/pricing">For properties</a>
		{#if authStore.isLoggedIn && authStore.isManager}
			<a class:active={isActive('/dashboard')} href="/dashboard">Dashboard</a>
		{/if}
		{#if authStore.isLoggedIn && !authStore.isManager}
			<a class:active={isActive('/bookings')} href="/bookings">My laundry</a>
		{/if}
	</nav>
	<div class="header-actions">
		<button
			class="theme-toggle"
			onclick={() => themeStore.toggle()}
			aria-label={themeStore.value === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
			aria-pressed={themeStore.value === 'dark'}
		></button>
		{#if authStore.isLoggedIn}
			<NotificationBell />
			<a class="user-name" href={authStore.isManager ? '/dashboard' : '/machines'}>{authStore.user.name}</a>
			<button class="text-button" onclick={logout}>Sign out</button>
		{:else}
			<button class="text-button" onclick={() => authModalStore.open('signin', 'resident')}>Sign in</button>
			<button class="button small" onclick={() => authModalStore.open('signup', 'resident')}>Get started</button>
		{/if}
	</div>
</header>
