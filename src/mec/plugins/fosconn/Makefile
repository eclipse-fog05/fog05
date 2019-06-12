all: atd
	dune build

atd:
	atdgen -j-std lib/fosconn_types.atd

clean:
	rm -rf lib/fosconn_types*.ml lib/fosconn_types*.mli
	dune clean
	rm -rf ./_build

install:
	opam install . --working-dir

#  uninstall:
#  	opam remove me-platform
# ocamlbuild -tag linkall -use-ocamlfind -pkgs 'base lwt apero-core lwt.unix yojson fos-im fos-meao-plugins fos-fim-api ppx_deriving.show dynlink lwt_ppx ppx_cstruct ppx_deriving.show' lib/fosconn.cmxs