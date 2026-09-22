const AUTO_DISMISS_MS = 6000;

class NoticeStore {
	message = $state('');
	timeoutId = null;

	show(message) {
		this.message = message;
		clearTimeout(this.timeoutId);
		this.timeoutId = setTimeout(() => this.clear(), AUTO_DISMISS_MS);
	}

	clear() {
		clearTimeout(this.timeoutId);
		this.message = '';
	}
}

export const noticeStore = new NoticeStore();
