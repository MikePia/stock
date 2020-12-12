# Pulling this project out of mothballs to make it independent from structjour. 
## The state of the software is development
* Make it a PyPi package when it approaches the point of general usefulness to:
    * get chart data from free apis or IBAPI
    * create an intraday candle chart with optional entries and exits

## The initial change is to move files
* next get rid of unused APIS that started charging or restricted usage too much
* Update to include Tiingo API which will use the new model using inheritance to provide the interface
* Change the other APIs to match the interface
* Re do the apichooser to use the new model (before that, will use a temporary function call that works with the current apichooser)

* Note that generally this software is in use in structjour now and I will keep  it more or less in sync with this project during development