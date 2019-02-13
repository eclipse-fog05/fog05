all: atd
	 dune build

atd:
	atdgen -t src/fos/fos-im/agent_types.atd
	atdgen -j src/fos/fos-im/agent_types.atd
	atdgen -v src/fos/fos-im/agent_types.atd
	atdgen -t src/fos/fos-im/types.atd
	atdgen -j src/fos/fos-im/types.atd
	atdgen -v src/fos/fos-im/types.atd
	atdgen -t src/fos/fos-im/types_record.atd
	atdgen -j src/fos/fos-im/types_record.atd
	atdgen -v src/fos/fos-im/types_record.atd
	atdgen -t src/fos/fos-im/im.atd
	atdgen -j src/fos/fos-im/im.atd
	atdgen -v src/fos/fos-im/im.atd

clean:
	rm -rf src/fos/fos-im/agent_types*.ml src/fos/fos-im/agent_types*.mli
	rm -rf src/fos/fos-im/types*.ml src/fos/fos-im/types*.mli
	rm -rf src/fos/fos-im/im_*.ml*
	rm -rf ./bin
	dune clean
	rm -rf agent


install:
	mkdir ./bin
	cp _build/default/src/fos/fos-cli-ng/fos_cli_ng.exe ./bin/fos-cli-ng
	cp _build/default/src/fos/fos-cat/fos_cat.exe ./bin/fos-cat
	cp _build/default/src/fos/fos-agent/fos_agent.exe ./bin/fos-agent
	cp _build/default/src/fos/fos-spawner/spawner.exe ./bin/fos-spawner

uninstall:
	rm -rf ./bin