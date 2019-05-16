all:
	dune build
	# ocamlbuild -tag linkall -use-ocamlfind -pkgs 'base lwt apero-core lwt.unix yojson fos-im fos-meao-plugins fos-fim-api ppx_deriving.show dynlink lwt_ppx ppx_cstruct ppx_deriving.show' lib/fosconn.cmxs

# atd:
# 	atdgen -t meao/rest_types.atd
# 	atdgen -j-std meao/rest_types.atd
# 	atdgen -v meao/rest_types.atd

clean:
	# rm -rf meao/rest_types*.ml meao/rest_types*.mli
	dune clean
	rm -rf ./_build

install:
	opam install . --working-dir

#  uninstall:
#  	opam remove me-platform
