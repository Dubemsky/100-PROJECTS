# Day 10 — Expense Tracker

A desktop expense tracker built with `customtkinter`. Log what you spend, see totals and a category breakdown, and keep monthly budgets per category.

1. Add an expense with an amount, category, date, and optional note, then click Add Expense
2. Click any expense in the history list to edit it or delete it
3. The top panel shows what you've spent this month and all time
4. Use the date range buttons (This Week, This Month, This Year, All Time) to filter the history and breakdown
5. The History, Breakdown, and Budgets tabs show your expenses, a pie chart by category, and spending against monthly budgets
6. Click a category on the Budgets tab to set its monthly limit. Going over turns the bar red
7. Click Export CSV to save every expense to a CSV file

Expenses are saved to `expenses.json`, budgets to `budgets.json`, both in this folder.

## How to run

Make sure you've completed the [setup steps](../README.md#setup) in the root folder first, then:

```
python3 main.py
```
