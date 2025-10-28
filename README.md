
## Commands

### Set watchman to send updates to CircuitPython board

```bash
watchman watch-project .
watchman -- trigger . copy-to-CIRCUITPY '*.py' -- sh -c 'cp *.py /media/CIRCUITPY'
```

Delete with:

```bash
watchman trigger-del . copy-to-CIRCUITPY
```

## Resources
The base of this project is
https://learn.adafruit.com/matrix-portal-scoreboard/overview. That code snippet
is MIT licensed so this project is MIT licensed.

The [matrixportal
lib](https://github.com/adafruit/Adafruit_CircuitPython_MatrixPortal) is
copied into this repo, mostly for development help.

```
$ git clone https://github.com/adafruit/Adafruit_CircuitPython_MatrixPortal lib/
<delete everything but the adafruit_matrixportal directory>
```
