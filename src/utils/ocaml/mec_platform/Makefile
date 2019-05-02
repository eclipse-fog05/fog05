all: atd
	dune build

atd:
	atdgen -t me_platform/rest_types.atd
	atdgen -j-std me_platform/rest_types.atd
	atdgen -v me_platform/rest_types.atd
	atdgen -t me_platform/dns_types.atd
	atdgen -j-std me_platform/dns_types.atd
	atdgen -v me_platform/dns_types.atd

clean:
	rm -rf me_platform/rest_types*.ml me_platform/rest_types*.mli
	rm -rf me_platform/dns_types*.ml me_platform/dns_types*.mli
	dune clean
	rm -rf ./_build

install:
	opam install .

#  uninstall:
#  	opam remove me-platform
