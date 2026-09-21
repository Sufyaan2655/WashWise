<script>
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import Header from '$lib/components/Header.svelte';
	import Notice from '$lib/components/Notice.svelte';
	import AuthModal from '$lib/components/AuthModal.svelte';
	import { authStore } from '$lib/stores/auth.svelte.js';
	import { machinesStore } from '$lib/stores/machines.svelte.js';
	import { notificationsStore } from '$lib/stores/notifications.svelte.js';

	let { children } = $props();

	onMount(async () => {
		await authStore.restore();
		await machinesStore.load();
		if (authStore.isLoggedIn) await notificationsStore.load();
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>WASHWISE — laundry, on your time</title>
	<meta name="description" content="A better laundry experience for apartment communities." />
</svelte:head>

<Header />
<Notice />
{@render children()}
<AuthModal />
