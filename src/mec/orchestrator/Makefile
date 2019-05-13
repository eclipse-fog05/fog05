all:
	dune build

# atd:
# 	atdgen -t meao/rest_types.atd
# 	atdgen -j-std meao/rest_types.atd
# 	atdgen -v meao/rest_types.atd

clean:
	# rm -rf meao/rest_types*.ml meao/rest_types*.mli
	dune clean
	rm -rf ./_build

install:
	opam install .

#  uninstall:
#  	opam remove me-platform
