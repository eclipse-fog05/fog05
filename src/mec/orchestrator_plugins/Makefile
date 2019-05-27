all:atd
	dune build

atd:
	atdgen -j-std lib/pl_types.atd

clean:
	rm -rf lib/pl_types*.ml lib/pl_types*.mli
	dune clean
	rm -rf ./_build

install:
	opam install .

 uninstall:
	opam remove fos-meao-plugins