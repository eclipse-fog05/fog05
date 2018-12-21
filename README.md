# fog05

Unifies compute/networking fabric end-to-end

Thanks to its plugin architecture can manage near everything

See inside [Wiki](https://github.com/eclipse/fog05/wiki) for more detailed information

See also [Introduction](https://github.com/eclipse/fog05/blob/master/Introduction.md) for more information

Inside [plugins](./plugins) there are some plugins for entity

### master

The version on master does not use Cyclone DDS for communication between nodes
You need to install YAKS API from pip

```
pip3 install yaks==0.1.0
```

You need a running YAKS server to use it.

YAKS can be found [here](https://www.dropbox.com/s/1tmbubzahzy4eex/yaksd.tar.gz)

#### 0.1.3 


For the version that uses Cyclone DDS go to branch [0.1.3](https://github.com/eclipse/fog05/tree/0.1.3)
See [Installation](https://github.com/eclipse/fog05/wiki/Installation) for installation instructions

### Interact with the nodes

In the wiki you can find information about:

- [Python3 API](https://github.com/eclipse/fog05/wiki/fog05-Python-API)
- [CLI Interface](https://github.com/eclipse/fog05/wiki/CLI-Interface)


### Contributing

If you want to contribute, please read information in [CONTRIBUTING.md](./CONTRIBUTING.md)

And take a look to [TODO.md](./TODO.md)
