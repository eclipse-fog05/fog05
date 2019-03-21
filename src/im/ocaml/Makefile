all: atd
	 dune build

atd:
	atdgen -t fos-im/agent_types.atd
	atdgen -j-std fos-im/agent_types.atd
	atdgen -v fos-im/agent_types.atd
	atdgen -t fos-im/fos_types.atd
	atdgen -j-std fos-im/fos_types.atd
	atdgen -v fos-im/fos_types.atd
	atdgen -t fos-im/fos_records_types.atd
	atdgen -j-std fos-im/fos_records_types.atd
	atdgen -v fos-im/fos_records_types.atd
	atdgen -t fos-im/im.atd
	atdgen -j-std fos-im/im.atd
	atdgen -v fos-im/im.atd

clean:
	rm -rf fos-im/agent_types*.ml fos-im/agent_types*.mli
	rm -rf fos-im/fos_types*.ml fos-im/fos_types*.mli
	rm -rf fos-im/fos_records_types*.ml fos-im/fos_records_types*.mli
	rm -rf fos-im/types_record*.ml fos-im/types_record*.mli
	rm -rf fos-im/im*.ml*
	dune clean
	rm -rf ./_build


install:
	opam install .
uninstall:
	opam remove fos-im