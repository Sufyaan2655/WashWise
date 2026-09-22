const STORAGE_KEY = 'washwise-theme';

function initial() {
	if (typeof document === 'undefined') return 'light';
	return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
}

let theme = $state(initial());

function apply(value) {
	theme = value;
	if (typeof document !== 'undefined') {
		document.documentElement.setAttribute('data-theme', value);
		localStorage.setItem(STORAGE_KEY, value);
	}
}

export const themeStore = {
	get value() {
		return theme;
	},
	toggle() {
		apply(theme === 'dark' ? 'light' : 'dark');
	}
};
