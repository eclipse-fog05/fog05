.PHONY: all debug clean deb rpm

all:
	cargo build --all-targets --release

debug:
	cargo build --all-targets
	cp ./target/debug/fosctl ./fosctl

deb:
	cargo deb

rpm:
	cargo rpm init
	cargo rpm build

clean:
	cargo clean