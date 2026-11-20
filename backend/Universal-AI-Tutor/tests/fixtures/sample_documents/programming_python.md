# Python Programming Essentials

## Data Types and Variables

### Basic Data Types

Python has several built-in data types:

1. **Numeric Types**
   - `int`: Integer numbers (e.g., 42, -17, 0)
   - `float`: Decimal numbers (e.g., 3.14, -0.001, 2.0)
   - `complex`: Complex numbers (e.g., 3+4j)

2. **Text Type**
   - `str`: Strings (e.g., "hello", 'world', """multi-line""")

3. **Boolean Type**
   - `bool`: True or False

4. **Sequence Types**
   - `list`: Ordered, mutable collection [1, 2, 3]
   - `tuple`: Ordered, immutable collection (1, 2, 3)
   - `range`: Sequence of numbers range(10)

5. **Mapping Type**
   - `dict`: Key-value pairs {"name": "Alice", "age": 30}

6. **Set Types**
   - `set`: Unordered, unique elements {1, 2, 3}
   - `frozenset`: Immutable set

### Variable Assignment

```python
# Simple assignment
x = 10
name = "Alice"

# Multiple assignment
a, b, c = 1, 2, 3

# Swap values
x, y = y, x
```

## Control Flow

### Conditional Statements

```python
# If-elif-else
if condition:
    # code block
elif other_condition:
    # code block
else:
    # code block

# Ternary operator
result = value_if_true if condition else value_if_false
```

### Loops

```python
# For loop
for item in iterable:
    # code block

# While loop
while condition:
    # code block

# Loop control
break     # Exit loop
continue  # Skip to next iteration
```

## Functions

### Defining Functions

```python
def function_name(parameter1, parameter2):
    """Docstring describing function."""
    # function body
    return result

# Default parameters
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

# Variable-length arguments
def sum_all(*args):
    return sum(args)

# Keyword arguments
def person_info(**kwargs):
    for key, value in kwargs.items():
        print(f"{key}: {value}")
```

### Lambda Functions

```python
# Anonymous function
square = lambda x: x**2

# Often used with map, filter, reduce
numbers = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x**2, numbers))
evens = list(filter(lambda x: x % 2 == 0, numbers))
```

## Data Structures

### Lists

```python
# Create list
my_list = [1, 2, 3, 4, 5]

# Common operations
my_list.append(6)       # Add to end
my_list.insert(0, 0)    # Insert at position
my_list.pop()           # Remove and return last
my_list.remove(3)       # Remove first occurrence of 3
my_list.sort()          # Sort in place
my_list.reverse()       # Reverse in place

# List comprehension
squares = [x**2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
```

### Dictionaries

```python
# Create dictionary
person = {
    "name": "Alice",
    "age": 30,
    "city": "New York"
}

# Access values
name = person["name"]
age = person.get("age", 0)  # Returns 0 if key not found

# Add/update
person["email"] = "alice@example.com"

# Dictionary comprehension
squares = {x: x**2 for x in range(5)}
```

### Sets

```python
# Create set
my_set = {1, 2, 3, 4, 5}

# Set operations
set_a = {1, 2, 3}
set_b = {3, 4, 5}

union = set_a | set_b           # {1, 2, 3, 4, 5}
intersection = set_a & set_b    # {3}
difference = set_a - set_b      # {1, 2}
```

## Object-Oriented Programming

### Classes

```python
class Person:
    """A simple Person class."""
    
    # Class variable
    species = "Homo sapiens"
    
    def __init__(self, name, age):
        """Constructor."""
        self.name = name    # Instance variable
        self.age = age
    
    def greet(self):
        """Instance method."""
        return f"Hello, I'm {self.name}"
    
    @classmethod
    def from_birth_year(cls, name, birth_year):
        """Class method."""
        age = 2026 - birth_year
        return cls(name, age)
    
    @staticmethod
    def is_adult(age):
        """Static method."""
        return age >= 18

# Usage
person = Person("Alice", 30)
print(person.greet())
```

### Inheritance

```python
class Student(Person):
    """Student inherits from Person."""
    
    def __init__(self, name, age, student_id):
        super().__init__(name, age)
        self.student_id = student_id
    
    def study(self, subject):
        return f"{self.name} is studying {subject}"
```

## Exception Handling

```python
try:
    # Code that might raise exception
    result = 10 / 0
except ZeroDivisionError as e:
    # Handle specific exception
    print(f"Error: {e}")
except Exception as e:
    # Handle any other exception
    print(f"Unexpected error: {e}")
else:
    # Executed if no exception
    print("Success!")
finally:
    # Always executed
    print("Cleanup")

# Raising exceptions
def validate_age(age):
    if age < 0:
        raise ValueError("Age cannot be negative")
    return age
```

## File I/O

```python
# Reading files
with open("file.txt", "r") as f:
    content = f.read()              # Read entire file
    lines = f.readlines()           # Read all lines
    for line in f:                  # Iterate line by line
        print(line.strip())

# Writing files
with open("output.txt", "w") as f:
    f.write("Hello, World!\n")
    f.writelines(["line1\n", "line2\n"])

# Appending
with open("log.txt", "a") as f:
    f.write("New log entry\n")
```

## Common Built-in Functions

```python
# Type conversion
int("42")      # String to int
float("3.14")  # String to float
str(42)        # Any to string
list("abc")    # String to list ['a', 'b', 'c']

# Sequence operations
len([1, 2, 3])           # Length: 3
min([3, 1, 2])           # Minimum: 1
max([3, 1, 2])           # Maximum: 3
sum([1, 2, 3])           # Sum: 6
sorted([3, 1, 2])        # Returns sorted list
reversed([1, 2, 3])      # Returns reverse iterator

# Type checking
isinstance(42, int)      # True
type(42)                 # <class 'int'>

# Input/Output
input("Enter name: ")    # Read user input
print("Hello", end="")   # Print without newline
```

## Best Practices

1. **PEP 8 Style Guide**
   - Use 4 spaces for indentation
   - Snake_case for variables and functions
   - PascalCase for classes
   - Maximum line length: 79 characters

2. **Documentation**
   - Write docstrings for functions and classes
   - Use type hints for clarity
   - Keep code self-documenting

3. **Error Handling**
   - Use specific exceptions
   - Don't use bare except clauses
   - Clean up resources with context managers

4. **Code Organization**
   - One class per file for large projects
   - Group related functions
   - Use modules and packages
