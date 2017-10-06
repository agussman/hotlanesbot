# Background

# Research
Current Toll data is available from https://www.expresslanes.com/on-the-road

Looking at the Networking activity we submit the form and see a call to:
https://www.expresslanes.com/on-the-road-api?ods%5B%5D=1021

```
{
ods: [
1021
],
rates: [
{
od: "1021",
rate: "1.95",
road: "495",
direction: "N",
duration: "8"
}
]
}
```

Further digging reveals the call:
https://www.expresslanes.com/cache/roadway/entry_exit.js?1457483614

This data files contains all viable exit points for an entry point (e.g., all paths through the network).
It's a little wonky because it's broken up into Northbound and Southbound, it's almost like there's two roads.

Most importantly, it contains the `ods` codes that uniquely identify an Entrance/Exit pair.

Awesome, we can query multiple `ods` prices at a time:
https://www.expresslanes.com/on-the-road-api?ods[]=1038&ods[]=1044&ods[]=1195

Let's grab all the `ods` values with `jq` for style points:
$ cat data/entry_exit.json | jq '.[] | .[] | .[] | .exits | .[] | .ods | .[]'

