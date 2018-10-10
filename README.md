## Description

Simple cli and API implementation for Vizio SmartCast TV. Mainly created for 
integration with [HASS](http://home-assistant.io).

## Installation

Either through pip

```
pip3 install git+https://github.com/vkorn/pyvizio.git@master
```

or checkout repo and run 

```
pip3 install -I .
```

## CLI Usage

To avoid repeating IP and Auth params, you can add them to environment variables as `VIZIO_IP` 
and `VIZIO_AUTH` respectively

### Pairing

First, find your device (yeah, I'm too lazy to add another cli group)
```
pyvizio --ip=0 --auth=0 discover
```

and note it's IP address. Using this IP address request pairing procedure:

```
pyvizio --ip={ip} pair
```

lookup PIN code on your TV and note challenge token in console.

> Better to have device turned on as it's "forgetting" PIN sometimes if it was 
turned off prior to pairing command

Using these dafa finalize pairing procedure
```
pyvizio --ip={ip} pair-finish --token={challenge_token} --pin={tv_pin} 
```
If everything done correctly, you should see new connected device named `Python Vizio` 
in Vizio SmartCast mobile APP 


> You'll need auth code for any further commands

### Turning on/off

```
pyvizio --ip={ip} --auth={auth_code} power {on|off|toggle}
```

To get current power state simply call

```
pyvizio --ip={ip} --auth={auth_code} power
``` 

### Volume operations

You could change volume

```
pyvizio --ip={ip} --auth={auth_code} volume {up|down} amount
```

and get current level (0-100)

```
pyvizio --ip={ip} --auth={auth_code} volume_current
```

In addition mute command is available

```
get_inputmute {on|off|toggle}
```

### Switching channels
```
pyvizio --ip={ip} --auth={auth_code} channel {up|down|prev} amount
```

### Input sources

You can get current source 

```
pyvizio --ip={ip} --auth={auth_code} input_get
```

List all connected devices

```
pyvizio --ip={ip} --auth={auth_code} input_list
```

And using `Name` column from this list switch input


```
pyvizio --ip={ip} --auth={auth_code} input --name={name}
```

Other options is to circle through all inputs
```
pyvizio --ip={ip} --auth={auth_code} input_next
``` 

## Contribution

Thanks for great research uploaded [here](https://github.com/exiva/Vizio_SmartCast_API) and 
absolutely awesome SSDP discovery [snippet](https://gist.github.com/dankrause/6000248)
