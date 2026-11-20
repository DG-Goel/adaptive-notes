# Calculus Fundamentals

## Derivatives

A derivative represents the rate of change of a function. For a function f(x), the derivative f'(x) is defined as:

$$f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}$$

### Power Rule

For any function f(x) = x^n where n is a constant:

$$\frac{d}{dx}(x^n) = nx^{n-1}$$

Example: If f(x) = x³, then f'(x) = 3x²

### Product Rule

For two differentiable functions u(x) and v(x):

$$\frac{d}{dx}[u(x) \cdot v(x)] = u'(x) \cdot v(x) + u(x) \cdot v'(x)$$

### Chain Rule

For composite functions:

$$\frac{d}{dx}[f(g(x))] = f'(g(x)) \cdot g'(x)$$

## Integration

Integration is the inverse operation of differentiation. The indefinite integral is written as:

$$\int f(x) \, dx = F(x) + C$$

where F'(x) = f(x) and C is the constant of integration.

### Fundamental Theorem of Calculus

The definite integral from a to b equals:

$$\int_a^b f(x) \, dx = F(b) - F(a)$$

### Common Integrals

1. $$\int x^n \, dx = \frac{x^{n+1}}{n+1} + C$$ (for n ≠ -1)
2. $$\int e^x \, dx = e^x + C$$
3. $$\int \frac{1}{x} \, dx = \ln|x| + C$$
4. $$\int \sin(x) \, dx = -\cos(x) + C$$
5. $$\int \cos(x) \, dx = \sin(x) + C$$

## Applications

### Finding Maximum and Minimum

To find extrema:
1. Find critical points by setting f'(x) = 0
2. Use the second derivative test: if f''(x) > 0, it's a minimum; if f''(x) < 0, it's a maximum
3. Check endpoints of the interval

### Area Under a Curve

The area between a curve y = f(x) and the x-axis from x = a to x = b is:

$$A = \int_a^b f(x) \, dx$$

### Related Rates

When two or more quantities are related and changing with respect to time, we can use the chain rule to find how their rates of change are related.

Example: If the radius of a circle is increasing at 2 cm/s, how fast is the area increasing when r = 5 cm?

- Given: dr/dt = 2 cm/s
- Find: dA/dt when r = 5
- Solution: A = πr², so dA/dt = 2πr(dr/dt) = 2π(5)(2) = 20π cm²/s
