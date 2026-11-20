# Python Basics

## Variables

In Python, variables are containers for storing data values. Unlike some other programming languages, Python has no command for declaring a variable. A variable is created the moment you first assign a value to it.

Example:
```python
x = 5
y = "Hello"
```

Python variables do not need explicit declaration to reserve memory space. The declaration happens automatically when you assign a value to a variable.

## Data Types

Python has the following built-in data types:

- **int**: Integer numbers (e.g., 5, -3, 1000)
- **float**: Floating point numbers (e.g., 3.14, -0.5, 2.0)
- **str**: Strings (e.g., "hello", 'world')
- **bool**: Boolean values (True or False)
- **list**: Ordered, mutable collection [1, 2, 3]
- **tuple**: Ordered, immutable collection (1, 2, 3)
- **dict**: Key-value pairs {"name": "John", "age": 30}

## Functions

A function is a block of code which only runs when it is called. You can pass data, known as parameters, into a function. A function can return data as a result.

Example:
```python
def greet(name):
    return f"Hello, {name}!"

message = greet("Alice")
print(message)  # Output: Hello, Alice!
```

Functions help organize code and make it reusable.
