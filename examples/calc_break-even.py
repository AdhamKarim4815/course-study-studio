"""Every number the break-even example lesson shows, computed once.

Sunny Cup is a fictional lemonade stand. Run: python3 calc_break-even.py
"""
import math

price, vc, fixed = 2.50, 0.70, 460.00

cm = price - vc                       # contribution margin per cup
ratio = cm / price                    # CM ratio
be_units = fixed / cm                 # break-even, exact
be_cups = math.ceil(be_units)         # you can't sell part of a cup: round UP
be_sales = fixed / ratio              # break-even in sales dollars
short_255 = 255 * cm - fixed          # contribution at 255 cups minus fixed costs
over_256 = be_cups * cm - fixed       # ... and at 256 cups
wrong = fixed / price                 # the trap: dividing by the price
cost_400 = fixed + vc * 400           # total cost line end point for the chart

print(f'CM per cup            {cm:.2f}')
print(f'CM ratio              {ratio:.0%}  ({ratio:.2f})')
print(f'Break-even, exact     {be_units:.2f} cups')
print(f'Break-even, rounded   {be_cups} cups')
print(f'Break-even sales      {be_sales:.2f}')
print(f'At 255 cups           CM {255 * cm:.2f}, result {short_255:.2f}')
print(f'At 256 cups           CM {be_cups * cm:.2f}, result {over_256:.2f}')
print(f'Trap: fixed / price   {wrong:.0f} cups')
print(f'Chart: sales at 400 cups {price * 400:.0f}, total cost at 400 cups {cost_400:.0f}')

# Your turn: iced tea
t_price, t_vc, t_fixed = 3.00, 0.90, 420.00
t_cm = t_price - t_vc
t_ratio = t_cm / t_price
print(f'Your turn: CM {t_cm:.2f}, ratio {t_ratio:.0%}, break-even {t_fixed / t_cm:.0f} cups, sales {t_fixed / t_ratio:.0f}')

# Practice question: a bake sale table
b_price, b_vc, b_fixed = 1.50, 0.40, 88.00
b_cm = b_price - b_vc
print(f'Practice: CM {b_cm:.2f}, break-even {b_fixed / b_cm:.0f} cookies, profit at 120 cookies {120 * b_cm - b_fixed:.2f}')
