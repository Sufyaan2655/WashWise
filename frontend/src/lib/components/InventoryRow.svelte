<script>
	let { machine, onToggle } = $props();
</script>

<div class="inventory-row">
	<div class="machine-symbol small-symbol {machine.type.toLowerCase()}">{machine.icon}</div>
	<div><b>{machine.name}</b><span>{machine.duration} min · ${machine.price.toFixed(2)} per cycle</span></div>
	<span class:available={machine.status === 'Available'} class="status">{machine.status}</span>
	<button class="row-action" onclick={() => onToggle(machine)}>
		{machine.status === 'Maintenance' ? 'Set active' : 'Set maintenance'}
	</button>
</div>
