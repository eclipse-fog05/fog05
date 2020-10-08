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

	if len(args) < 1 {
		zenoh_addr, exists := os.LookupEnv("ZENOH")
		if !exists {
			panic(fmt.Errorf("ZENOH environment variable is not set!!"))
		}

		zenoh := fmt.Sprintf("tcp/%s:7447", zenoh_addr)

		app, err := NewAppFromParams("9191", "0.0.0.0", zenoh)
		check(err)
		app.Initialize()
		app.Run()

	} else {
		data, err := ioutil.ReadFile(args[0])
		check(err)
		conf := Configuration{}
		json.Unmarshal(data, &conf)

		app, err := NewApp(conf)
		check(err)
		app.Initialize()
		app.Run()
	}

}
