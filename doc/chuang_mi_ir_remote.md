### Chuang Mi IR remote
- Copy custom_components/switch/chuangmi_ir.py to your home assistant configuration folder.
- Please follow the instructions on [Retrieving the Access Token](https://home-assistant.io/components/xiaomi/#retrieving-the-access-token) to get the API token to use in the configuration.yaml file.
- To add the Chuang Mi IR remote to your installation, add the following to your `configuration.yaml` file:

```
switch:
  - platform: chuangmi_ir
    name: "Living Room IR Remote"
    host: !secret chuangmi_ip
    token: !secret chuangmi_key
    switches:
      reciever:
        command_on: ''
        command_off: ''
```

- To learn infrared commands, you can use the "learn command" service. The service domain is `chuangmi`, the service is called `learn_command_YOUR_DEVICE_IP`.
- If you have called the service, press a key of your ordinary IR remote pointing to the Chuangmi IR remote controller.
- You will receive a notification at home assistant ("States"). It contains the captured infrared command (f.e. *Z6VLAAkCAABpAgAAYgYAAKYIAACJEQAAoSMAAKScAABYeQEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABFAQEBAQEBAQEhISEhISEhIQEBISEBAQEBISEBASEhISFhNXE1AQ==*).
- Copy the captured command and use it at `command_on` or `command_off`.

```
- platform: chuangmi_ir
  host: !secret chuangmi_ip
  name: "livingroomirremote"
  token: !secret chuangmi_key
  switches:
    reciever:
      command_on: ''
      command_off: ''
    wcfan:
      name: 'wcfan'
      command_on: 'Z6VLAAkCAABpAgAAYgYAAKYIAACJEQAAoSMAAKScAABYeQEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABFAQEBAQEBAQEhISEhISEhIQEBISEBAQEBISEBASEhISFhNXE1AQ=='
      command_off: 'Z6VHAPEBAACBAgAASQYAAIYIAABqEQAAySMAAECcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABFAQEBAQEBAQEhISEhISEhIQEBASEhAQEBISEhAQEhISFhNQE='
```
- Already learned commands with the MiHome App can be extracted from /data/data/com.xiaomi.smarthome/files/IR_REMOTE_DID_device.json.