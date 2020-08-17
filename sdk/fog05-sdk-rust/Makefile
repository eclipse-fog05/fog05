all:
	protoc --rust_out src/im src/im/data.proto
	cargo build

clean:
	cargo clean
	rm src/im/data.rs