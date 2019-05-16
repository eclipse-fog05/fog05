all:atd
	dune build

atd:
	atdgen -j-std lib/types.atd

clean:
	# rm -rf meao/rest_types*.ml meao/rest_types*.mli
	dune clean
	rm -rf ./_build

install:
	opam install .

 uninstall:
	opam remove fos-meao-plug