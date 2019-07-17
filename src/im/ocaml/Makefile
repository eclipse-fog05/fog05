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

	atdgen -j-std fos-im/router.atd
	# atdgen -t fos-im/fdu.atd
	atdgen -j-std fos-im/fdu.atd

	atdgen -j-std fos-im/nfv.atd

	atdgen -j-std fos-im/mec.atd

	atdgen -j-std fos-im/mec_interfaces.atd


clean:
	rm -rf fos-im/agent_types*.ml fos-im/agent_types*.mli
	rm -rf fos-im/fos_types*.ml fos-im/fos_types*.mli
	rm -rf fos-im/fos_records_types*.ml fos-im/fos_records_types*.mli
	rm -rf fos-im/types_record*.ml fos-im/types_record*.mli
	rm -rf fos-im/fdu*.ml fos-im/fdu*.mli
	rm -rf fos-im/nfv*.ml*
	rm -rf fos-im/mec*.ml*
	rm -rf fos-im/router*.ml*
	dune clean
	rm -rf ./_build


install:
	opam install . --working-dir
uninstall:
	opam remove fos-im