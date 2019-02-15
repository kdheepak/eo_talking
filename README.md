# eo_talking

### Setup

```sh
conda install -c gmlc-tdc helics
pip install git+git://github.com/GMLC-TDC/helics-cli.git@master
```

### Run

```sh
helics run --path config.json
```

### Issue

Runs correctly every now and then.
Run the above multiple times and it'll hang on every third or so run.
CTRL-C to exit

`broker.log` shows that federation is entered before all federates have registered themselves.

