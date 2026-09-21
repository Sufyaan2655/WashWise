<script>
	import { fly } from 'svelte/transition';
	import { noticeStore } from '../stores/notice.svelte.js';
</script>

{#if noticeStore.message}
	<div class="notice" transition:fly={{ y: -10, duration: 220 }}>
		<span>✦</span>{noticeStore.message}
		<button onclick={() => noticeStore.clear()} aria-label="Dismiss">×</button>
	</div>
{/if}
