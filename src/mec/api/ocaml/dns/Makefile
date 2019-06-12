all: atd
	dune build

atd:
	atdgen -j-std lib/dns_types.atd

clean:
	rm -rf lib/dns_types*.ml lib/dns_types*.mli
	dune clean
	rm -rf ./_build

install:
	opam install .

uninstall:
	opam remove fos-dns