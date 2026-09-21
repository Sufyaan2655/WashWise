class AuthModalStore {
	visible = $state(false);
	mode = $state('signin'); // 'signin' | 'signup'
	audience = $state('resident'); // 'resident' | 'manager'

	open(mode = 'signin', audience = 'resident') {
		this.mode = mode;
		this.audience = audience;
		this.visible = true;
	}

	close() {
		this.visible = false;
	}
}

export const authModalStore = new AuthModalStore();
