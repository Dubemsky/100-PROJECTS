# Day 7 — Currency Converter

A desktop currency converter built with `customtkinter`, using live exchange rates from [Frankfurter.app](https://www.frankfurter.app/) (free, no API key needed).

1. Enter an amount, then click the FROM/TO buttons to search and pick a currency from all 30 supported
2. Click Convert to see the result, plus the live exchange rate (e.g. "1 USD = 0.9234 EUR")
3. Click the ⇄ button to instantly swap the FROM and TO currencies
4. Rates are cached to `rates_cache.json` after every successful conversion, so a pair you've already converted still works offline (marked "offline, cached ...")

## How to run

Make sure you've completed the [setup steps](../README.md#setup) in the root folder first, then:

```
python3 main.py
```
