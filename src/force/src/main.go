package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
)

func check(e error) {
	if e != nil {
		panic(e)
	}
}

func main() {
	args := os.Args[1:]
	fmt.Println(args)

	data, err := ioutil.ReadFile(args[0])
	check(err)
	conf := Configuration{}
	json.Unmarshal(data, &conf)

	app, err := NewApp(conf)
	check(err)
	app.Initialize()
	app.Run()

}
