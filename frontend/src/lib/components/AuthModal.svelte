<script>
	import { fade, fly } from 'svelte/transition';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authStore } from '../stores/auth.svelte.js';
	import { authModalStore } from '../stores/authModal.svelte.js';
	import { noticeStore } from '../stores/notice.svelte.js';
	import { machinesStore } from '../stores/machines.svelte.js';
	import { bookingsStore } from '../stores/bookings.svelte.js';
	import { apiFetch } from '../api.js';

	let loading = $state(false);
	let formError = $state('');
	let email = $state('');
	let password = $state('');
	let buildings = $state([]);
	let signup = $state({ name: '', email: '', phone: '', card: '', password: '', building_id: '' });

	onMount(async () => {
		try {
			buildings = await apiFetch('/buildings');
		} catch {
			buildings = [];
		}
	});

	function close() {
		authModalStore.close();
		password = '';
		formError = '';
	}

	async function login() {
		if (!email || !password) return (formError = 'Enter your email and password to continue.');
		loading = true;
		formError = '';
		try {
			const user = await authStore.login(email, password);
			close();
			await machinesStore.load();
			if (user.role === 'manager') {
				await goto('/dashboard');
			} else {
				await bookingsStore.load();
				await goto('/machines');
			}
			noticeStore.show(`Welcome back, ${user.name}.`);
		} catch (error) {
			formError = error.message;
		} finally {
			loading = false;
		}
	}

	async function createAccount() {
		if (!signup.name || !signup.email || !signup.password) {
			formError = 'Enter your name, email, and password.';
			return;
		}
		loading = true;
		formError = '';
		try {
			await apiFetch('/users', {
				method: 'POST',
				body: JSON.stringify({
					building_id: Number(signup.building_id),
					name: signup.name,
					email: signup.email,
					phone_number: signup.phone || null,
					password: signup.password,
					role: 'tenant'
				})
			});
			formError = 'Account created successfully. You can now sign in.';
			email = signup.email;
			password = '';
			authModalStore.mode = 'signin';
			signup = { name: '', email: '', phone: '', card: '', password: '', building_id: '' };
		} catch (error) {
			formError = error.message;
		} finally {
			loading = false;
		}
	}
</script>

{#if authModalStore.visible}
	<div class="modal-backdrop" transition:fade={{ duration: 160 }} role="presentation">
		<div class="auth-modal" transition:fly={{ y: 18, duration: 220 }} role="dialog" aria-modal="true">
			<button class="close" onclick={close} aria-label="Close">×</button>
			<div class="auth-title">
				<p class="kicker">
					{authModalStore.mode === 'signup' ? 'Resident account' : authModalStore.audience === 'manager' ? 'Property workspace' : 'Welcome back'}
				</p>
				<h2>
					{authModalStore.mode === 'signup' ? 'Laundry on your terms.' : authModalStore.audience === 'manager' ? 'Manage your building.' : 'Good to see you.'}
				</h2>
				<p>
					{authModalStore.mode === 'signup' ? 'Create your free account in a few quick steps.' : authModalStore.audience === 'manager' ? 'Use your developer or admin credentials.' : 'Sign in to book your next laundry time.'}
				</p>
			</div>

			{#if authModalStore.mode === 'signin'}
				<div class="role-switch">
					<button class:chosen={authModalStore.audience === 'resident'} onclick={() => (authModalStore.audience = 'resident')}>Resident</button>
					<button class:chosen={authModalStore.audience === 'manager'} onclick={() => (authModalStore.audience = 'manager')}>Developer / admin</button>
				</div>
				<label>Email<input type="email" bind:value={email} placeholder={authModalStore.audience === 'manager' ? 'admin@property.com' : 'you@example.com'} /></label>
				<label>Password<input type="password" bind:value={password} placeholder="Enter password" /></label>
				<button class="button full-width" onclick={login} disabled={loading}>
					{loading ? 'Signing in…' : `Sign in as ${authModalStore.audience === 'manager' ? 'property team' : 'resident'}`} <span>→</span>
				</button>
				{#if authModalStore.audience === 'resident'}
					<p class="auth-footer">New to WASHWISE? <button onclick={() => (authModalStore.mode = 'signup')}>Create an account</button></p>
				{/if}
			{:else}
				<div class="form-grid">
					<label>Full name<input bind:value={signup.name} placeholder="Maya Carter" /></label>
					<label>Email<input type="email" bind:value={signup.email} placeholder="maya@email.com" /></label>
					<label>Mobile number<input type="tel" bind:value={signup.phone} placeholder="(555) 000-0000" /></label>
					<label>Building
						<select bind:value={signup.building_id}>
							<option value="">Choose your building</option>
							{#each buildings as building}
								<option value={building.building_id}>{building.name}</option>
							{/each}
						</select>
					</label>
				</div>
				<label>
					Password
					<input type="password" bind:value={signup.password} placeholder="Create a password" required />
				</label>
				<label>
					Card number <span class="optional">(optional for now)</span>
					<input bind:value={signup.card} inputmode="numeric" placeholder="•••• •••• •••• 1234" />
				</label>
				<button class="button full-width" onclick={createAccount} disabled={loading}>
					{loading ? 'Creating account...' : 'Create resident account'} <span>→</span>
				</button>
				<p class="auth-footer">Already have an account? <button onclick={() => (authModalStore.mode = 'signin')}>Sign in</button></p>
			{/if}

			{#if formError}<p class="form-message">{formError}</p>{/if}
		</div>
	</div>
{/if}
