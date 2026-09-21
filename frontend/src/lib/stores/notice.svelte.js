class NoticeStore {
	message = $state('');

	show(message) {
		this.message = message;
	}

	clear() {
		this.message = '';
	}
}

export const noticeStore = new NoticeStore();
