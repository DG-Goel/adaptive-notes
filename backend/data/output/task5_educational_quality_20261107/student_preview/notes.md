> UNVERIFIED PREVIEW — semantic and educational review required.

# Study notes: java

*Generated from assembled notes*

---

## JDK

### JDK

JDK stands for Java Development Kit and is a software development environment for building Java applications. It includes a compiler, a Java Runtime Environment, and other tools.

*[Knowledge ID: DEF_0001 | Sources: T0001]*

The Java Development Kit (JDK) can be downloaded for various platforms such as Linux, macOS, and Windows.

*[Knowledge ID: FCT_0002 | Sources: T0001]*

The course will cover installing the necessary tools to build Java applications, basics of Java, how Java code is executed, and building simple algorithms.

*[Knowledge ID: FCT_0003 | Sources: T0001]*

The instructor, Mosh, has two decades of experience as a software engineer and has taught over 3 million people how to code.

*[Knowledge ID: FCT_0004 | Sources: T0001]*

## function

### function

functions are a block of code that performs a task

*[Knowledge ID: DEF_0020 | Sources: T0002]*

> **Example: we can have a function for sending emails to people**
> 
> we can have a function for sending emails to people

*[Knowledge ID: EXM_0002 | Sources: T0002]*

> **Example: we can have a function for converting someone's weight in pounds to kilograms**
> 
> we can have a function for converting someone's weight in pounds to kilograms

*[Knowledge ID: EXM_0003 | Sources: T0002]*

The smallest building block in Java programs are functions.

*[Knowledge ID: FCT_0135 | Sources: T0002]*

Void is a reserved keyword in Java used as a return type for functions that do not return a value.

*[Knowledge ID: FCT_0005 | Sources: T0002]*

> Procedure correctness not reviewed; do not assume this is a correct solution.

#### Flowchart: Download and install IntelliJ IDEA

```mermaid
flowchart TD
    N0["Click on the download link for IntelliJ IDEA Community Edition"]
    N1["Drag and drop the downloaded application onto the Applications folder"]
    N0 --> N1
```

*[Knowledge ID: PRC_0006 | Sources: T0002]*

## Class

### Class

a container for one or more related functions

*[Knowledge ID: DEF_0021 | Sources: T0003]*

### Method

a function that is part of a class

*[Knowledge ID: DEF_0002 | Sources: T0003]*

### Pascal naming convention

the first letter of every word should be uppercase in class names

*[Knowledge ID: DEF_0003 | Sources: T0003]*

> Claim review: INCONCLUSIVE — The claim that every word is lowercase is not established by its truncated/ambiguous source segment. Continuation and later camel-notation explanation require review; do not certify this rule.

### Camel naming convention

the first letter of every word should be lowercase in method names

*[Knowledge ID: DEF_0004 | Sources: T0003]*

In Java, the left brace is placed on the same line where the function is defined.

*[Knowledge ID: FCT_0136 | Sources: T0003]*

Every Java program should have at least one function called main, which is the entry point.

*[Knowledge ID: FCT_0006 | Sources: T0003]*

Functions in Java must belong to a class.

*[Knowledge ID: FCT_0007 | Sources: T0003]*

Every Java program should have at least one class that contains the main function.

*[Knowledge ID: FCT_0008 | Sources: T0003]*

Java classes and methods have access modifiers such as public and private.

*[Knowledge ID: FCT_0009 | Sources: T0003]*

The public access modifier is most commonly used for classes and methods.

*[Knowledge ID: FCT_0010 | Sources: T0003]*

A minimal Java program consists of a main class and a main method inside that class.

*[Knowledge ID: FCT_0011 | Sources: T0003]*

## command line application

### command line application

an application that we can run from the command line; it doesn't have a graphical user interface or a GUI

*[Knowledge ID: DEF_0022 | Sources: T0004]*

### package

a namespace for related classes; the base package for a Java project is the domain name of your company in reverse

*[Knowledge ID: DEF_0023 | Sources: T0004]*

JDK version 12 is selected for the project

*[Knowledge ID: FCT_0137 | Sources: T0004]*

The base package for the project is set to com.codewithmarsh

*[Knowledge ID: FCT_0138 | Sources: T0004]*

## package statement

### package statement

Specifies the package to which the class belongs; it is terminated by a semicolon.

*[Knowledge ID: DEF_0024 | Sources: T0005]*

### main method

A public static method named main with a void return type and a single parameter; it serves as the entry point of a Java program.

*[Knowledge ID: DEF_0025 | Sources: T0005]*

### comment

Text prefixed with // that explains code and is not executed.

*[Knowledge ID: DEF_0026 | Sources: T0005]*

### System class

A class defined in the java.lang package that provides access to system resources such as standard output.

*[Knowledge ID: DEF_0027 | Sources: T0005]*

All Java files should have the .java extension.

*[Knowledge ID: FCT_0139 | Sources: T0005]*

Every statement in Java must be terminated with a semicolon.

*[Knowledge ID: FCT_0140 | Sources: T0005]*

The main method must be declared static and have a void return type.

*[Knowledge ID: FCT_0141 | Sources: T0005]*

Comments in Java start with // and are ignored by the compiler.

*[Knowledge ID: FCT_0142 | Sources: T0005]*

The System class resides in the java.lang package.

*[Knowledge ID: FCT_0143 | Sources: T0005]*

## Source T0006

The dot operator is used to access members (fields, methods, etc.) of a class in Java.

*[Knowledge ID: FCT_0001 | Sources: T0006]*

In IntelliJ, a field is indicated by the icon "F" and a method is indicated by the icon "M".

*[Knowledge ID: FCT_0144 | Sources: T0006]*

A string literal in Java must be surrounded by double quotes.

*[Knowledge ID: FCT_0145 | Sources: T0006]*

When a Java program is run in IntelliJ, the code is first compiled into Java bytecode by the Java compiler that comes with the Java Development Kit.

*[Knowledge ID: FCT_0146 | Sources: T0006]*

After compilation, the bytecode is executed to produce the program's output.

*[Knowledge ID: FCT_0147 | Sources: T0006]*

## Java bytecode is platform independent

The compiled Java bytecode can run on Windows, macOS, Linux, or any operating system that has a Java Runtime Environment because it is not tied to a specific hardware architecture.

*[Knowledge ID: EXP_0001 | Sources: T0007]*

The JVM takes Java bytecode and converts it into the native code required by the underlying operating system, enabling the same bytecode to execute on different platforms.

*[Knowledge ID: EXP_0002 | Sources: T0007]*

Java bytecode is platform independent and can run on any OS with a Java Runtime Environment.

*[Knowledge ID: FCT_0148 | Sources: T0007]*

The JVM translates Java bytecode into native code for the host operating system.

*[Knowledge ID: FCT_0149 | Sources: T0007]*

> Procedure correctness not reviewed; do not assume this is a correct solution.

#### Flowchart: Compile a Java source file

```mermaid
flowchart TD
    N0["Open a terminal #40;or command prompt#41; in the folder containing the source file."]
    N1["Run the Java compiler: #96;javac Main.java#96; #40;case#8209;sensitive on macOS#47;Linux#41;."]
    N0 --> N1
```

*[Knowledge ID: PRC_0005 | Sources: T0007]*

> Procedure correctness not reviewed; do not assume this is a correct solution.

**Run a compiled Java program:**

- In the terminal, execute the JVM with the class name: `java Main`.

*[Knowledge ID: PRC_0328 | Sources: T0007]*

> Procedure correctness not reviewed; do not assume this is a correct solution.

**Locate compiled class files:**

- In the project panel, open the `out` folder to see the compiled `.class` files under the package hierarchy.

*[Knowledge ID: PRC_0007 | Sources: T0007]*

## Source T0008

Java was developed by James Gosling in 1995 at Sun Microsystems which was later acquired by Oracle in 2010.

*[Knowledge ID: FCT_0150 | Sources: T0008]*

It was originally called oke after an oak tree that stood outside Gosling's office later it was renamed to green and was finally renamed to Java inspired by Java coffee that's why its logo looks like this.

*[Knowledge ID: FCT_0151 | Sources: T0008]*

We have four editions of Java for building different kinds of applications.

*[Knowledge ID: FCT_0152 | Sources: T0008]*

Java standard edition is the core Java platform which is what we're using in this course it contains all of the libraries that every Java developer must learn.

*[Knowledge ID: FCT_0153 | Sources: T0008]*

Java Enterprise Edition is used for building very large-scale and distributed systems it is built on top of java standard edition and provides additional libraries for building fault tolerant distributed multi-tiered software.

*[Knowledge ID: FCT_0154 | Sources: T0008]*

Java micro Edition is a subset of Java standard edition designed for mobile devices so it has libraries specific to mobile devices.

*[Knowledge ID: FCT_0155 | Sources: T0008]*

Java card is used in smart cards.

*[Knowledge ID: FCT_0156 | Sources: T0008]*

The latest version of Java is Java standard edition 12 which was released just a few months ago in March 2019.

*[Knowledge ID: FCT_0157 | Sources: T0008]*

Java has close to 9 million developers worldwide.

*[Knowledge ID: FCT_0158 | Sources: T0008]*

Currently about 3 billion mobile phones run Java as well as 120 million TV sets and every blu-ray player according to indeed.com.

*[Knowledge ID: FCT_0159 | Sources: T0008]*

The average salary of a Java developer is just over $100,000 per year in the US.

*[Knowledge ID: FCT_0160 | Sources: T0008]*

## object-oriented programming

### object-oriented programming

a style of programming used in most if not all Java applications

*[Knowledge ID: DEF_0028 | Sources: T0009]*

### control flow statements

statements that are used to build algorithms, including various types of conditional statements and loops

*[Knowledge ID: DEF_0029 | Sources: T0009]*

The course is a four-part Java series, each part about three to four hours long.

*[Knowledge ID: FCT_0161 | Sources: T0009]*

The first part teaches the fundamentals of programming with Java.

*[Knowledge ID: FCT_0162 | Sources: T0009]*

The type system in Java includes primitives, strings, booleans, and arrays.

*[Knowledge ID: FCT_0163 | Sources: T0009]*

By the end of the first part, you will build a mortgage calculator.

*[Knowledge ID: FCT_0164 | Sources: T0009]*

The second part covers control flow statements, conditional statements, loops, and adds data validation to the mortgage calculator.

*[Knowledge ID: FCT_0165 | Sources: T0009]*

Clean coding techniques are taught to make code clean and maintainable.

*[Knowledge ID: FCT_0166 | Sources: T0009]*

The course teaches how to find and fix errors in Java programs and how to package them for deployment.

*[Knowledge ID: FCT_0167 | Sources: T0009]*

The third part covers core Java API useful classes in the standard Java library.

*[Knowledge ID: FCT_0168 | Sources: T0009]*

The fourth part covers advanced Java features such as streams, threads, and database programming.

*[Knowledge ID: FCT_0169 | Sources: T0009]*

A final project involves building a mortgage calculator on your own using the learned material.

*[Knowledge ID: FCT_0012 | Sources: T0009]*

## camelCase notation

we should capitalize the first letter of every word except the first word

*[Knowledge ID: CON_0001 | Sources: T0010]*

### variable

variables are used to temporarily store data in computer's memory

*[Knowledge ID: DEF_0030 | Sources: T0010]*

### type

the type of our variable then we give it a name or a label this is also called an identifier

*[Knowledge ID: DEF_0031 | Sources: T0010]*

### assignment operator

this equal sign is called the assignment operator

*[Knowledge ID: DEF_0032 | Sources: T0010]*

### initialization

we're initializing this variable which means we're giving it an initial value

*[Knowledge ID: DEF_0005 | Sources: T0010]*

int or integer is the type of this variable so in this variable we can only store integers which are whole numbers like 1 2 3 4 numbers that don't have a decimal point

*[Knowledge ID: EXP_0006 | Sources: T0010]*

we give it a name or a label this is also called an identifier because we use it to identify our variable

*[Knowledge ID: EXP_0007 | Sources: T0010]*

you always have to initialize our variables before reading them

*[Knowledge ID: EXP_0008 | Sources: T0010]*

this is called the camelCase notation so we should capitalize the first letter of every word except the first word

*[Knowledge ID: EXP_0009 | Sources: T0010]*

> **Example: variable initialization**
> 
> int age = 30

*[Knowledge ID: EXM_0010 | Sources: T0010]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
reading them so with this line we're storing number 30 somewhere in computer's memory and we're assigning this label to that memory location now on line 7 instead of printing hello world we can print the value of the age variable take a look so I'm gonna run this program using ctrl + R there you go now we see 30 on the terminal beautiful we can also change the value of our variable so after we initialize it per house we can change it to 35 now when we run this program again we see it 35

*[Knowledge ID: EXM_0011 | Sources: T0010]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
reading them so with this line we're storing number 30 somewhere in computer's memory and we're assigning this label to that memory location now on line 7 instead of printing hello world we can print the value of the age variable take a look so I'm gonna run this program using ctrl + R there you go now we see 30 on the terminal beautiful we can also change the value of our variable so after we initialize it per house we can change it to 35 now when we run this program again we see it 35

*[Knowledge ID: EXM_0012 | Sources: T0010]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
beautiful we can also initialize multiple variables on the same line but this is something that I don't recommend because it makes your code ugly and hard to read here is an example we can declare another variable like temperature and set it to 20 so using a comma we can declare multiple variables on the same line now even though this is technically possible it's not something that I recommend so it's always better to declare one variable on each line like this we can also copy the value of one

*[Knowledge ID: EXM_0013 | Sources: T0010]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
variable into another here is an example let me delete these variables and declare a new variable called my age we set it to 30 and then we declare another variable like her age and we set it to my age so now when we print her age we're gonna see 30 take a look so on line seven recapping the value of this variable into this other variable now one thing I want you to pay attention to here is the convention I have used for naming our variables as I told you before this is called the camelcase

*[Knowledge ID: EXM_0014 | Sources: T0010]*

variables must be initialized before they can be read

*[Knowledge ID: FCT_0015 | Sources: T0010]*

declaring multiple variables on the same line makes code harder to read and is not recommended

*[Knowledge ID: FCT_0016 | Sources: T0010]*

## meaningful variable names help understand code

Using meaningful and descriptive names for variables improves code readability and comprehension.

*[Knowledge ID: EXP_0072 | Sources: T0011]*

byte takes one byte of memory and stores values from -128 to 127

*[Knowledge ID: FCT_0170 | Sources: T0011]*

short takes two bytes of memory and stores values up to 32,000

*[Knowledge ID: FCT_0171 | Sources: T0011]*

int (integer) takes four bytes of memory and allows storing values up to two billion

*[Knowledge ID: FCT_0172 | Sources: T0011]*

long takes eight bytes of memory and can store even larger numbers

*[Knowledge ID: FCT_0173 | Sources: T0011]*

float takes four bytes for storing decimal numbers

*[Knowledge ID: FCT_0174 | Sources: T0011]*

double takes eight bytes for storing decimal numbers

*[Knowledge ID: FCT_0175 | Sources: T0011]*

char takes two bytes and stores a single character, supporting international letters

*[Knowledge ID: FCT_0176 | Sources: T0011]*

boolean stores true or false values

*[Knowledge ID: FCT_0177 | Sources: T0011]*

Underscores can be used in numeric literals to improve readability, separating groups of three digits

*[Knowledge ID: FCT_0178 | Sources: T0011]*

## int

### int

by default Java sees whole numbers as integers

*[Knowledge ID: DEF_0033 | Sources: T0012]*

### long

to represent a whole number larger than the int range, add an uppercase or lowercase L suffix; uppercase L is preferred because lowercase l looks like 1

*[Knowledge ID: DEF_0034 | Sources: T0012]*

### float

by default Java sees numbers with a decimal point as double; to store a decimal number as float, add an uppercase or lowercase F suffix

*[Knowledge ID: DEF_0035 | Sources: T0012]*

### double

default type for numbers with a decimal point in Java

*[Knowledge ID: DEF_0036 | Sources: T0012]*

### char

stores a single character; the character literal must be surrounded by single quotes

*[Knowledge ID: DEF_0037 | Sources: T0012]*

### String

stores a series of characters; string literals are surrounded by double quotes

*[Knowledge ID: DEF_0006 | Sources: T0012]*

### boolean

stores a true or false value

*[Knowledge ID: DEF_0007 | Sources: T0012]*

### reserved keywords

words that are part of the Java language syntax (e.g., public, static, void, class, package) and cannot be used as identifiers for variables, classes, or methods

*[Knowledge ID: DEF_0008 | Sources: T0012]*

> **Example: long literal**
> 
> 3L

*[Knowledge ID: EXM_0009 | Sources: T0012]*

> **Example: float literal**
> 
> 3.5F

*[Knowledge ID: EXM_0107 | Sources: T0012]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
boolean variable called is eligible is this person eligible for loan or not we said this to true or false these are the boolean values now note that all these words coded in orange are reserved keywords in Java just like public static void class package these are all reserved keywords so we cannot use these reserved keywords the name our variables classes and methods in the last tutorial you learned that we use primitive types to store simple values like numbers boolean values or single

*[Knowledge ID: EXM_0108 | Sources: T0012]*

integer number too large

*[Knowledge ID: FCT_0179 | Sources: T0012]*

incompatible types required float but found double

*[Knowledge ID: FCT_0013 | Sources: T0012]*

## primitive type

### primitive type

primitive types are the eight basic data types built into Java that are not reference types

*[Knowledge ID: DEF_0038 | Sources: T0013]*

### reference type

reference types are all types other than the eight primitive types and represent objects created from classes

*[Knowledge ID: DEF_0039 | Sources: T0013]*

### package

a package is a namespace that groups related classes and allows the same class name to exist in different packages without conflict

*[Knowledge ID: DEF_0040 | Sources: T0013]*

### import

import is a statement that makes a class from another package available in the current source file

*[Knowledge ID: DEF_0041 | Sources: T0013]*

### object

an object is an instance of a class

*[Knowledge ID: DEF_0042 | Sources: T0013]*

### class

a class is a blueprint or template for creating objects

*[Knowledge ID: DEF_0043 | Sources: T0013]*

primitive types are allocated and released automatically by the Java Runtime Environment, whereas reference types require explicit memory allocation with the new operator and are reclaimed automatically later

*[Knowledge ID: EXP_0073 | Sources: T0013]*

Java has eight primitive types

*[Knowledge ID: FCT_0180 | Sources: T0013]*

All other types in Java are reference types

*[Knowledge ID: FCT_0181 | Sources: T0013]*

To use a class from a different package you must import it

*[Knowledge ID: FCT_0182 | Sources: T0013]*

Packages create a namespace that prevents class name conflicts

*[Knowledge ID: FCT_0183 | Sources: T0013]*

The new operator allocates memory for a reference type object

*[Knowledge ID: FCT_0184 | Sources: T0013]*

Objects are instances of classes

*[Knowledge ID: FCT_0185 | Sources: T0013]*

Members of an object are accessed using the dot operator

*[Knowledge ID: FCT_0014 | Sources: T0013]*

The getTime method returns the time component of a Date object

*[Knowledge ID: FCT_0186 | Sources: T0013]*

## Source T0014

A primitive type does not have members, so using the dot operator on a primitive variable shows nothing.

*[Knowledge ID: FCT_0187 | Sources: T0014]*

Reference types are classes that have members (fields and methods) which can be accessed with the dot operator.

*[Knowledge ID: FCT_0188 | Sources: T0014]*

Primitive types store simple values, while reference types store complex objects.

*[Knowledge ID: FCT_0189 | Sources: T0014]*

Variables of primitive types hold independent copies of values; changing one variable does not affect another variable that was assigned its value.

*[Knowledge ID: FCT_0190 | Sources: T0014]*

Variables of reference types hold references to objects; assigning one reference variable to another makes both refer to the same object, so changes via one reference affect the other.

*[Knowledge ID: FCT_0191 | Sources: T0014]*

## Reference types in Java store a reference (address) to an object in memory rather than the actual object value.

When a variable of a reference type is declared, it holds the address of the object in memory. Assigning one reference variable to another copies the reference, so both variables point to the same object. Updating the object through any reference is reflected when accessed via the other reference.

*[Knowledge ID: EXP_0074 | Sources: T0015]*

Primitive variables store the actual value in their memory location, while reference variables store the address of an object.

*[Knowledge ID: FCT_0192 | Sources: T0015]*

Assigning one reference variable to another copies the reference, causing both variables to refer to the same object.

*[Knowledge ID: FCT_0193 | Sources: T0015]*

Changes made to an object via one reference variable are visible through any other reference variable that points to the same object.

*[Knowledge ID: FCT_0194 | Sources: T0015]*

## Accessing members of a String object

String is a class, its members are accessed using the dot operator.

*[Knowledge ID: EXP_0075 | Sources: T0016]*

> **Example: String concatenation using the plus operator**
> 
> message + "!!"

*[Knowledge ID: EXM_0109 | Sources: T0016]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
see if our message ends with two exclamation marks now instead of printing the message let's print this expression here so let's run the program we get true so this method that we have called here returns a boolean value which can be true or false we also have another method starts with let's take a look now in this case we get false because our message doesn't start with two exclamation marks another useful method is length so we can call that to get the length of a string which is the number

*[Knowledge ID: EXM_0110 | Sources: T0016]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
of characters so message dot length take a look so in this string we have 13 characters and this is useful in situations where you want to check the length of the input

*[Knowledge ID: EXM_0004 | Sources: T0016]*

String class is defined in the java.lang package and is automatically imported.

*[Knowledge ID: FCT_0195 | Sources: T0016]*

String variables can be initialized with a string literal without using the new operator; using new String is redundant.

*[Knowledge ID: FCT_0196 | Sources: T0016]*

Strings are reference types in Java; using a literal is shorthand for creating a String object.

*[Knowledge ID: FCT_0197 | Sources: T0016]*

String concatenation can be done using the plus operator.

*[Knowledge ID: FCT_0198 | Sources: T0016]*

String class has method endsWith that returns a boolean indicating if the string ends with a given suffix.

*[Knowledge ID: FCT_0199 | Sources: T0016]*

String class has method startsWith that returns a boolean indicating if the string starts with a given prefix.

*[Knowledge ID: FCT_0200 | Sources: T0016]*

String class has method length that returns the number of characters in the string.

*[Knowledge ID: FCT_0201 | Sources: T0016]*

## parameter

### parameter

Parameters are the placeholders defined in a method signature.

*[Knowledge ID: DEF_0044 | Sources: T0017]*

### argument

Arguments are the actual values passed to a method when it is called.

*[Knowledge ID: DEF_0045 | Sources: T0017]*

### immutable string

In Java, strings cannot be changed after they are created; any method that appears to modify a string actually returns a new string object.

*[Knowledge ID: DEF_0046 | Sources: T0017]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
first II in this message is 1 now what if you pass a character or a string that doesn't exist in this message let's say Skye we get negative 1 so with this method we can check to see if a string contains certain characters or words or sentences and so on another useful method is replace and with this we can replace one or more characters with something else for example we can replace any exclamation marks with let's say a store so this replace metal has two parameters one is target the other is
replacement and here we're passing two values for these parameters here's the first value here is the second value and we have separated these values using a comma now in programming terms we refer to this values as arguments a lot of programmers don't know the difference between parameters and arguments parameters are the holes that we define in our methods arguments are the actual values that we pass to these methods so in this case target and replacement or parameters but exclamation mark and
asterisk are arguments now let's run this program and see what happens so our explanation marks are replaced with stars now what is important here is that this method does not modify our original string it returns a new string so if we print our original string right after SRU T tab message you can see the original string is not changed because in Java strings are immutable we cannot mutate them we cannot change them so any methods that modify a string will always return a new string object okay

*[Knowledge ID: EXM_0111 | Sources: T0017]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
by the user for example you might have a sign-up form with a username field you can check the length of someone's username and give them an error if the username is longer than let's say 20 characters pretty useful we also have another method that is index of and this returns the index of the first occurrence of the character or the string that we pass here for example if you pass H the index of H is 0 so let's run the program there you go we get 0 if you pass e we get 1 because the index of the
first II in this message is 1 now what if you pass a character or a string that doesn't exist in this message let's say Skye we get negative 1 so with this method we can check to see if a string contains certain characters or words or sentences and so on another useful method is replace and with this we can replace one or more characters with something else for example we can replace any exclamation marks with let's say a store so this replace metal has two parameters one is target the other is

*[Knowledge ID: EXM_0005 | Sources: T0017]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
we also have another useful method to lowercase let's take a look so to lowercase converts all characters to lowercase and once again you can see that the original string is not affected because this method returns a new string okay we also have two uppercase and another useful method is trim trim and with this we can get rid of extra white spaces that can be at the beginning or the end of a string sometimes our users type unnecessary spaces in form fields so using the trim method we can get rid
of these white spaces let me show you so I'm gonna add a couple of spaces before and after our message now when we trim it these white spaces are gonna

*[Knowledge ID: EXM_0006 | Sources: T0017]*

The length of a username can be checked and an error shown if it exceeds a specified limit (e.g., 20 characters).

*[Knowledge ID: FCT_0202 | Sources: T0017]*

indexOf returns the index of the first occurrence of a character or substring, or -1 if it does not exist.

*[Knowledge ID: FCT_0203 | Sources: T0017]*

replace takes two arguments: the target to be replaced and the replacement value.

*[Knowledge ID: FCT_0204 | Sources: T0017]*

String methods such as replace, toLowerCase, toUpperCase, and trim return new string objects and do not modify the original string.

*[Knowledge ID: FCT_0205 | Sources: T0017]*

toLowerCase converts all characters in a string to lowercase.

*[Knowledge ID: FCT_0206 | Sources: T0017]*

toUpperCase converts all characters in a string to uppercase.

*[Knowledge ID: FCT_0207 | Sources: T0017]*

trim removes extra whitespace at the beginning and end of a string.

*[Knowledge ID: FCT_0208 | Sources: T0017]*

## escape sequence

### escape sequence

An escape sequence is a combination of characters that starts with a backslash (\) and represents a special character in a Java string, such as a double quote, backslash, newline, or tab.

*[Knowledge ID: DEF_0047 | Sources: T0018]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
so in this tutorial I'm gonna show you how to include these special characters in your strings so here we have the string hello Marsh let's say we want to surround Marsh with double quotes now here's the problem if we add a double quote here Java compiler thinks this is the termination of our string so it doesn't stand what we have after that's why we have a compilation error the fixes problem we need to prefix this double code with a backslash so using this backslash we have escaped the double

*[Knowledge ID: EXM_0112 | Sources: T0018]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
quote now one more time let's add backslash double code here now let's run the program and see what we get so we get hello Marsh in double quote beautiful so double quote is one of those special characters that you need to be aware of another special character is backslash let's say we want to store the pass to a directory on a Windows machine so that will look like this C Drive backslash windows backslash whatever now if you want to store this in a string we need to escape each backslash let me
show you so C Drive backslash now we have a problem Java compiler thinks we're escaping the double code here so it thinks our string is not terminated with another double code but that's not what we want you want to add a backslash here so we need to prefix our backslash with another backslash now we type windows one more time something let's run the program so even though we have two backslashes in our code we actually see one backslash in a terminal window in other escape sequences backslash N

*[Knowledge ID: EXM_0113 | Sources: T0018]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
and we use that to add a new line to our strings so let's change this to backslash N and run the program to see what happens now our string is broken down onto multiple lines by the first line we have C Drive then we have Windows so wherever we had a backslash n Java will insert a new line we can also add a tab in our strings so if you add backslash T here there will be a tab which means C Drive and windows let's take a look so C Drive here we have a tab and then windows now in Java we have a

*[Knowledge ID: EXM_0114 | Sources: T0018]*

In Java strings, a backslash (\) is used to escape special characters such as double quote (\"), backslash (\\), newline (\n), and tab (\t).

*[Knowledge ID: FCT_0209 | Sources: T0018]*

Four commonly used escape sequences in Java are \" (double quote), \\ (backslash), \n (newline), and \t (tab).

*[Knowledge ID: FCT_0210 | Sources: T0018]*

## array

### array

an array is a reference type used to store a list of items such as numbers, people, or messages

*[Knowledge ID: DEF_0048 | Sources: T0019]*

to declare an array of integers you write int\[\] followed by the variable name

*[Knowledge ID: FCT_0211 | Sources: T0019]*

arrays are reference types and must be created with the new operator

*[Knowledge ID: FCT_0212 | Sources: T0019]*

the size (length) of an array is specified in square brackets after the new operator

*[Knowledge ID: FCT_0213 | Sources: T0019]*

array indices start at 0; the first element is accessed with index 0

*[Knowledge ID: FCT_0214 | Sources: T0019]*

accessing an index outside the array bounds (e.g., index 10 in a length‑5 array) throws an exception and crashes the program

*[Knowledge ID: FCT_0215 | Sources: T0019]*

printing an array directly (e.g., System.out.println(array)) yields a string based on the object's memory address, not its contents

*[Knowledge ID: FCT_0216 | Sources: T0019]*

the java.util.Arrays class provides a toString method that returns a readable representation of an array's items

*[Knowledge ID: FCT_0217 | Sources: T0019]*

the Arrays.toString method is overloaded for each primitive type and for reference types

*[Knowledge ID: FCT_0218 | Sources: T0019]*

## Source T0020

In an integer array, elements not explicitly initialized are set to 0 by default.

*[Knowledge ID: FCT_0219 | Sources: T0020]*

In a boolean array, elements default to false.

*[Knowledge ID: FCT_0220 | Sources: T0020]*

In a string array, elements default to an empty string.

*[Knowledge ID: FCT_0221 | Sources: T0020]*

Older syntax for creating and initializing an array uses the new operator and separate statements; newer syntax uses curly braces with the items listed inside.

*[Knowledge ID: FCT_0222 | Sources: T0020]*

The length of an array can be read using the array.length property.

*[Knowledge ID: FCT_0223 | Sources: T0020]*

Java arrays have a fixed size; once created, items cannot be added or removed.

*[Knowledge ID: FCT_0224 | Sources: T0020]*

To add or remove items dynamically, one should use collection classes instead of arrays.

*[Knowledge ID: FCT_0225 | Sources: T0020]*

Arrays can be sorted using the Arrays.sort method, which is overloaded with different parameter types.

*[Knowledge ID: FCT_0226 | Sources: T0020]*

Java supports multi‑dimensional arrays (e.g., two‑dimensional for matrices, three‑dimensional for cubes) useful in scientific computations.

*[Knowledge ID: FCT_0227 | Sources: T0020]*

## constant

### constant

A variable declared with the `final` keyword in Java, which cannot be changed after it is initialized.

*[Knowledge ID: DEF_0049 | Sources: T0021]*

A two‑dimensional array in Java requires two pairs of square brackets, one for each dimension.

*[Knowledge ID: FCT_0228 | Sources: T0021]*

To access an element in a two‑dimensional array you must supply two indexes: the row index followed by the column index.

*[Knowledge ID: FCT_0229 | Sources: T0021]*

`Arrays.deepToString` should be used to print the contents of a multi‑dimensional array, otherwise `toString` yields an unreadable string.

*[Knowledge ID: FCT_0230 | Sources: T0021]*

A two‑dimensional array can be initialized with curly‑brace syntax, where each row is itself an array literal.

*[Knowledge ID: FCT_0231 | Sources: T0021]*

When assigning a floating‑point literal to a `float` variable in Java, an `F` suffix is required (e.g., `3.14F`).

*[Knowledge ID: FCT_0232 | Sources: T0021]*

## final variable

### final variable

a variable declared with the keyword final, meaning its value cannot be changed after initialization

*[Knowledge ID: DEF_0050 | Sources: T0022]*

### constant

a final variable whose name is written in all capital letters by convention

*[Knowledge ID: DEF_0051 | Sources: T0022]*

### arithmetic expression

a piece of code that produces a value

*[Knowledge ID: DEF_0052 | Sources: T0022]*

### operand

a number or variable on which an arithmetic operator acts

*[Knowledge ID: DEF_0053 | Sources: T0022]*

### increment operator

operator (++) that increases the value of a numeric variable by 1

*[Knowledge ID: DEF_0054 | Sources: T0022]*

### decrement operator

operator (--) that decreases the value of a numeric variable by 1

*[Knowledge ID: DEF_0055 | Sources: T0022]*

Constants are written in all capital letters to distinguish them from regular variables

*[Knowledge ID: EXP_0076 | Sources: T0022]*

When two integers are divided, Java returns an integer result, discarding any fractional part

*[Knowledge ID: EXP_0077 | Sources: T0022]*

Casting one operand to double (or float) causes the division to be performed in floating‑point arithmetic

*[Knowledge ID: EXP_0078 | Sources: T0022]*

Postfix (x++) returns the original value then increments; prefix (++x) increments first then returns the new value

*[Knowledge ID: EXP_0010 | Sources: T0022]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
multiplication division and modulus which is the remainder of a division let's look at a few examples so I'm gonna declare an integer called result and here we can type 10 plus 3 now when we print result it's gonna be 13 pretty straightforward there you go so this is addition we also have subtraction multiplication division is an interesting one let's take a look so here the result is a whole number because in Java the division of two whole numbers is a whole number if you want to get a

*[Knowledge ID: EXM_0115 | Sources: T0022]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
multiplication division and modulus which is the remainder of a division let's look at a few examples so I'm gonna declare an integer called result and here we can type 10 plus 3 now when we print result it's gonna be 13 pretty straightforward there you go so this is addition we also have subtraction multiplication division is an interesting one let's take a look so here the result is a whole number because in Java the division of two whole numbers is a whole number if you want to get a

*[Knowledge ID: EXM_0116 | Sources: T0022]*

> Claim review: PARTIALLY\_SUPPORTED — Spoken casting demonstration does not supply the generated exact declaration and result comment. Show source explanation, retain generated snippet in audit.
> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
floating-point number here you need to convert these numbers to a float or a double let me show you so we prefix this number with parentheses and in parentheses we type double now we are casting or converting this number to a double similarly we should do that here and now we have a compilation error because on the left side we declared an integer but here the result of this expression is a double and by the way an expression is a piece of code that produces a value so what we have here is an

*[Knowledge ID: EXM_0117 | Sources: T0022]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
get 2 there you go we can apply this operator as a postfix or as a prefix and we get

*[Knowledge ID: EXM_0118 | Sources: T0022]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
get 2 there you go we can apply this operator as a postfix or as a prefix and we get

*[Knowledge ID: EXM_0015 | Sources: T0022]*

pi is a final variable (constant) in the example

*[Knowledge ID: FCT_0233 | Sources: T0022]*

division of two whole numbers yields a whole number in Java

*[Knowledge ID: FCT_0017 | Sources: T0022]*

casting an int to double allows floating‑point division

*[Knowledge ID: FCT_0018 | Sources: T0022]*

## Source T0023

When using the postfix increment operator (x++) in an assignment, the original value of x is assigned first and then x is incremented.

*[Knowledge ID: FCT_0234 | Sources: T0023]*

When using the prefix increment operator (++x) in an assignment, x is incremented first and then the new value is assigned.

*[Knowledge ID: FCT_0235 | Sources: T0023]*

The augmented assignment operator X += 2 is equivalent to X = X + 2.

*[Knowledge ID: FCT_0236 | Sources: T0023]*

In Java, multiplication and division have higher precedence than addition and subtraction; thus 10 + 3 * 2 evaluates to 16.

*[Knowledge ID: FCT_0237 | Sources: T0023]*

Parentheses override default precedence; (10 + 3) * 2 evaluates to 26.

*[Knowledge ID: FCT_0238 | Sources: T0023]*

Order of operations priority: parentheses first, then multiplication/division, then addition/subtraction.

*[Knowledge ID: FCT_0239 | Sources: T0024]*

Implicit casting automatically converts a short value to an int when assigned to an int variable.

*[Knowledge ID: FCT_0240 | Sources: T0024]*

Assigning a double literal to an int variable without an explicit cast causes a compilation error.

*[Knowledge ID: FCT_0241 | Sources: T0024]*

When an int is used in an expression with a double, the int is automatically cast to double.

*[Knowledge ID: FCT_0242 | Sources: T0024]*

## implicit casting

### implicit casting

implicit casting happens whenever you're not going to lose data; there is no chance for data loss

*[Knowledge ID: DEF_0056 | Sources: T0025]*

### explicit casting

explicit casting converts a value to a specified type, such as casting a floating‑point number to an integer to discard the fractional part

*[Knowledge ID: DEF_0057 | Sources: T0025]*

### wrapper class

a reference type that provides methods for converting between strings and primitive types, e.g., java.lang.Integer for the int primitive

*[Knowledge ID: DEF_0058 | Sources: T0025]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
point zero and then two point zero will be added to one point one okay so back to this chain here we're gonna have float and then double so as a general rule of thumb implicit casting happens whenever you're not gonna lose data there is no chance for data loss now what if you want Y to be an integer so in this example we don't care about the digits after the decimal point you want to see three on the terminal how should we do this this is where we should explicitly cast the result so we should

*[Knowledge ID: EXM_0119 | Sources: T0025]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
it takes a string and returns a short similarly we have float and double and obviously the name of these metas are different so here we have parse float so back to this example let's say we get X as a string and we want to convert it to an integer this is how we do it integer dot parse int we pass X here and then add it to take a look so we get 3 you might be curious why this matters why should we parse or convert a string to a number to add it to something else well pretty much in most

*[Knowledge ID: EXM_0120 | Sources: T0025]*

explicit casting can only happen between compatible numeric types; you cannot cast a string to a number directly

*[Knowledge ID: FCT_0243 | Sources: T0025]*

the Integer class provides a parseInt method that takes a string and returns an int

*[Knowledge ID: FCT_0244 | Sources: T0025]*

the Short class provides a parseShort method that takes a string and returns a short

*[Knowledge ID: FCT_0245 | Sources: T0025]*

user input from UI components is typically received as strings, requiring conversion to numeric types for arithmetic

*[Knowledge ID: FCT_0246 | Sources: T0025]*

## Math class

### Math class

The Math class is defined in the java.lang package, is always available without explicit import, and provides static methods for performing mathematical operations.

*[Knowledge ID: DEF_0059 | Sources: T0026]*

> **Example: round method with float**
> 
> Passing 1.1 as a float to Math.round returns 1 (stored in an int).

*[Knowledge ID: EXM_0121 | Sources: T0026]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
int and a second implementation it takes a double and returns a log so let's pass 1.1 as a float to this method and store the result in an integer like this now we print the result and we get one beautiful another useful method is seal or sealing which returns the smallest integer that is greater than or equal to this number so the ceiling of 1.1 is 2 now here we have a compilation error because this method returns a double but we're storing the result in an integer so here we need to explicitly

*[Knowledge ID: EXM_0122 | Sources: T0026]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
cast this to an integer and now you can see the ceiling of this number is 2 we have another useful method that is floor so the floor of a number is the largest integer that is smaller or equal to this number in this case it's gonna be 1 let's take a look there you go another useful method is max which returns the greater of two values and once again this method is overloaded so in the first implementation we get two integers we have other implementations for longs floats and doubles so let's

*[Knowledge ID: EXM_0123 | Sources: T0026]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
cast this to an integer and now you can see the ceiling of this number is 2 we have another useful method that is floor so the floor of a number is the largest integer that is smaller or equal to this number in this case it's gonna be 1 let's take a look there you go another useful method is max which returns the greater of two values and once again this method is overloaded so in the first implementation we get two integers we have other implementations for longs floats and doubles so let's

*[Knowledge ID: EXM_0124 | Sources: T0026]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
pass two integers here one and two this will return the greater number which is 2 there you go similar to this we have min is pretty straightforward in the useful method is random for generating a random value between 0 and 1 once again we get a compilation error because this method returns a double so let's change that to double now every time we run this program we get a different number and this number is a floating-point number between 0 to 1 now what if you want a number between 0 to let's

*[Knowledge ID: EXM_0125 | Sources: T0026]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
pass two integers here one and two this will return the greater number which is 2 there you go similar to this we have min is pretty straightforward in the useful method is random for generating a random value between 0 and 1 once again we get a compilation error because this method returns a double so let's change that to double now every time we run this program we get a different number and this number is a floating-point number between 0 to 1 now what if you want a number between 0 to let's
say 100 instead of 0 to 1 well we simply multiply this by 100 take a look so every time we run this we get a

*[Knowledge ID: EXM_0007 | Sources: T0026]*

Math.round is overloaded: one version takes a float and returns an int; another version takes a double and returns a long.

*[Knowledge ID: FCT_0247 | Sources: T0026]*

Math.ceil returns the smallest integer greater than or equal to the argument (as a double).

*[Knowledge ID: FCT_0248 | Sources: T0026]*

Math.floor returns the largest integer less than or equal to the argument (as a double).

*[Knowledge ID: FCT_0249 | Sources: T0026]*

Math.max returns the greater of two values and is overloaded for int, long, float, and double.

*[Knowledge ID: FCT_0250 | Sources: T0026]*

Math.min returns the smaller of two values and is overloaded for int, long, float, and double.

*[Knowledge ID: FCT_0251 | Sources: T0026]*

Math.random returns a double value uniformly distributed between 0.0 (inclusive) and 1.0 (exclusive).

*[Knowledge ID: FCT_0252 | Sources: T0026]*

## Implicit casting cannot convert a long value to an int because the long occupies 8 bytes while the int occupies 4 bytes.

When a method returns a long but the variable is declared as an int, implicit casting fails; explicit casting must be used if the programmer knows the value fits into the smaller type.

*[Knowledge ID: EXP_0079 | Sources: T0027]*

Math.random() returns a value between 0 (inclusive) and 1 (exclusive); casting that double to int truncates the fractional part, producing 0.

*[Knowledge ID: EXP_0080 | Sources: T0027]*

Wrap the expression (Math.random() * 100) in parentheses and then cast the result to int; otherwise only the fractional part is cast, resulting in zero.

*[Knowledge ID: EXP_0003 | Sources: T0027]*

Java provides the NumberFormat class (in java.text) to format numbers with currency symbols, grouping separators, or as percentages.

*[Knowledge ID: EXP_0004 | Sources: T0027]*

Math.round returns a long value.

*[Knowledge ID: FCT_0253 | Sources: T0027]*

Casting a long to an int requires explicit casting.

*[Knowledge ID: FCT_0254 | Sources: T0027]*

Math.random() generates a double between 0 (inclusive) and 1 (exclusive).

*[Knowledge ID: FCT_0255 | Sources: T0027]*

## Source T0028

NumberFormat is an abstract class and cannot be instantiated with the new operator.

*[Knowledge ID: FCT_0256 | Sources: T0028]*

A factory method (e.g., getCurrencyInstance) creates and returns an instance of NumberFormat.

*[Knowledge ID: FCT_0257 | Sources: T0028]*

The returned NumberFormat object can be stored in a variable of type NumberFormat.

*[Knowledge ID: FCT_0258 | Sources: T0028]*

NumberFormat.format is an overloaded method that can accept long, double, etc., and returns a formatted string.

*[Knowledge ID: FCT_0259 | Sources: T0028]*

When formatting as currency, the result includes a dollar sign, commas as thousand separators, and two decimal digits.

*[Knowledge ID: FCT_0260 | Sources: T0028]*

NumberFormat.getPercentInstance returns a NumberFormat instance specialized for formatting percentages.

*[Knowledge ID: FCT_0261 | Sources: T0028]*

## Source T0029

Shift+F6 is the shortcut for the Rename refactor menu on Mac.

*[Knowledge ID: FCT_0262 | Sources: T0029]*

Method chaining allows calling multiple methods in a single statement by using the dot operator on the returned object.

*[Knowledge ID: FCT_0263 | Sources: T0029]*

In Java, System.in is used to read input from the terminal window.

*[Knowledge ID: FCT_0264 | Sources: T0029]*

The Scanner class (java.util.Scanner) is used to read input from the user in Java.

*[Knowledge ID: FCT_0265 | Sources: T0029]*

Methods of the Scanner class for reading data start with the prefix "next" (e.g., nextInt, nextLine).

*[Knowledge ID: FCT_0266 | Sources: T0029]*

## Source T0030

The Scanner method nextByte() returns a byte value which can be stored in a byte variable.

*[Knowledge ID: FCT_0267 | Sources: T0030]*

When concatenating a String with a byte, Java performs implicit casting (implicit type conversion) of the byte to a String.

*[Knowledge ID: FCT_0268 | Sources: T0030]*

The Scanner method nextLine() adds a new line after the printed label because it reads the remainder of the line including the line separator.

*[Knowledge ID: FCT_0269 | Sources: T0030]*

If a floating‑point number (e.g., 20.1) is entered when using nextInt(), a runtime exception occurs because the method can only parse integer values.

*[Knowledge ID: FCT_0270 | Sources: T0030]*

To read a floating‑point number with Scanner, use nextFloat() or nextDouble() instead of nextInt().

*[Knowledge ID: FCT_0271 | Sources: T0030]*

Scanner.next() returns the next token (a sequence of characters up to whitespace).

*[Knowledge ID: FCT_0272 | Sources: T0030]*

Scanner.nextLine() reads the remainder of the current line, including spaces, whereas Scanner.next() reads only up to the next whitespace.

*[Knowledge ID: FCT_0273 | Sources: T0030]*

When reading a full name with spaces using Scanner, calling next() once returns only the first token; a second call to next() is needed to obtain the second token.

*[Knowledge ID: FCT_0274 | Sources: T0030]*

## Source T0031

The trim method removes leading and trailing whitespace from a string.

*[Knowledge ID: FCT_0275 | Sources: T0031]*

The next line method returns a string entered by the user, preserving spaces and tabs.

*[Knowledge ID: FCT_0276 | Sources: T0031]*

> Claim review: PARTIALLY\_SUPPORTED — Only a fragment was extracted. Source continues with another expression and exponent, partly referring to unavailable visuals; no full formula reconstructed.
> Formula fragment: VISUAL\_CONTEXT\_REQUIRED. Do not use as a complete equation.

mortgage equals principal multiplied by monthly interest rate

*[Knowledge ID: FRM_0003 | Sources: T0031]*

## Avoiding magic numbers

Using constants or final variables instead of literal numbers makes code more understandable for others, as literals like 12 may not be immediately clear.

*[Knowledge ID: EXP_0081 | Sources: T0032]*

Select data types based on the range of values needed; use int for principal amounts up to two billion, and float for small interest rates instead of double.

*[Knowledge ID: EXP_0082 | Sources: T0032]*

Descriptive variable names improve code readability; avoid short or ambiguous names like "MI" for monthly interest.

*[Knowledge ID: EXP_0083 | Sources: T0032]*

Declaring constants for months in a year (12) and percent (100) prevents magic numbers.

*[Knowledge ID: FCT_0277 | Sources: T0032]*

A scanner object can be used to read user input for principal, interest rate, and period.

*[Knowledge ID: FCT_0278 | Sources: T0032]*

## camel notation

### camel notation

capitalizing the first letter of every word except the first word in a variable name

*[Knowledge ID: DEF_0060 | Sources: T0033]*

The maximum number we want to support is 30, so one byte is sufficient to store the number 30 or anything smaller.

*[Knowledge ID: FCT_0279 | Sources: T0033]*

If a non‑numeric value (e.g., "XYZ") is entered, the mortgage calculator program crashes.

*[Knowledge ID: FCT_0280 | Sources: T0033]*

If a negative value is entered, the mortgage calculator program does not behave properly.

*[Knowledge ID: FCT_0281 | Sources: T0033]*

Conditional statements can be used to validate user‑entered values.

*[Knowledge ID: FCT_0282 | Sources: T0033]*

Primitive types store simple values, while reference types hold references to complex objects.

*[Knowledge ID: FCT_0283 | Sources: T0033]*

Two types of casting exist: implicit and explicit.

*[Knowledge ID: FCT_0284 | Sources: T0033]*

## boolean expression

### boolean expression

a piece of code that produces a boolean value true or false

*[Knowledge ID: DEF_0061 | Sources: T0034]*

### comparison operators

operators used to compare primitive values such as equality (==), inequality (!=), greater than (&gt;), greater than or equal (&gt;=), less than (&lt;), and less than or equal (&lt;=)

*[Knowledge ID: DEF_0062 | Sources: T0034]*

### logical operators

operators such as logical AND (&amp;&amp;), logical OR (||), and logical NOT (!) used for implementing real‑world rules

*[Knowledge ID: DEF_0063 | Sources: T0034]*

Control flow statements include conditional statements for making decisions, loops for repeated execution, and error handling constructs.

*[Knowledge ID: EXP_0084 | Sources: T0034]*

Logical operators (&amp;&amp;, ||, !) are used to combine or invert boolean expressions to implement complex decision rules.

*[Knowledge ID: EXP_0005 | Sources: T0034]*

> **Example: x == y**
> 
> When x and y have the same value, the expression x == y evaluates to true.

*[Knowledge ID: EXM_0126 | Sources: T0034]*

> **Example: x != y**
> 
> When x and y are equal, the expression x != y evaluates to false.

*[Knowledge ID: EXM_0127 | Sources: T0034]*

> **Example: x &lt;= y**
> 
> If X is less than or equal to Y, the expression evaluates to true.

*[Knowledge ID: EXM_0008 | Sources: T0034]*

The equality operator (==) compares two values and returns true if they are equal, otherwise false.

*[Knowledge ID: FCT_0285 | Sources: T0034]*

The inequality operator (!=) returns false when the two compared values are equal.

*[Knowledge ID: FCT_0286 | Sources: T0034]*

The expression X &lt;= Y evaluates to true when X is less than or equal to Y.

*[Knowledge ID: FCT_0287 | Sources: T0034]*

## Source T0035

The &amp;&amp; operator represents logical AND; the expression is true only if both conditions are true. Java evaluates the expression from left to right and stops evaluating further conditions if the first condition is false (short‑circuit evaluation).

*[Knowledge ID: FCT_0288 | Sources: T0035]*

The || operator represents logical OR; the expression is true if at least one of the conditions is true. Java evaluates the expression from left to right and stops evaluating further conditions if the first condition is true (short‑circuit evaluation).

*[Knowledge ID: FCT_0289 | Sources: T0035]*

The ! operator is the logical NOT operator; it reverses the boolean value of its operand.

*[Knowledge ID: FCT_0290 | Sources: T0035]*

## Using the NOT operator to invert a boolean value

The NOT operator reverses the value of a boolean variable or expression; if the variable is false, applying NOT makes it true.

*[Knowledge ID: EXP_0085 | Sources: T0036]*

Wrap the first condition in parentheses, then use the AND operator (&amp;&amp;) to combine it with the second condition, e.g., (highIncome || goodCredit) &amp;&amp; !hasCriminalRecord.

*[Knowledge ID: EXP_0086 | Sources: T0036]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
30 perhaps you want to display two messages to the user it's a hot day drink plenty of water otherwise if it's between 20 and 30 you want to print it's a nice day and otherwise we want to print it's a cold day so let's see how we can implement these rules in a Java program back to our main file we start by declaring a variable temperature we set it to 32 now we use an if statement followed by a pair of parentheses inside this parenthesis we type an expression or a boolean value so let's say temp
is greater than 30 now if this condition is true the statement that we had after this if statement will be executed so let's print it's a hot day let's run the program we get this message because temperature is greater than 30 now what if you want to print another message like drink plenty of water here we should add curly braces to define a code block so if this condition is true all the code that we have inside of this block would be executed let's add another message here drink water okay so

*[Knowledge ID: EXM_0128 | Sources: T0036]*

A boolean variable "hasCriminalRecord" is initially set to false.

*[Knowledge ID: FCT_0291 | Sources: T0036]*

If the first condition and the second condition are both true, the person is eligible for a new loan.

*[Knowledge ID: FCT_0292 | Sources: T0036]*

> Procedure correctness not reviewed; do not assume this is a correct solution.

#### Flowchart: Implement loan eligibility rule using boolean logic

```mermaid
flowchart TD
    N0["Declare boolean variable hasCriminalRecord and set it to false."]
    N1["Wrap the first part of the rule #40;high income OR good credit#41; in parentheses."]
    N2["Combine the first part with the NOT of hasCriminalRecord using the AND operator #40;#38;#38;#41;."]
    N3["If the combined expression evaluates to true, the applicant is eligible for the loan."]
    N0 --> N1
    N1 --> N2
    N2 --> N3
```

*[Knowledge ID: PRC_0329 | Sources: T0036]*

> Procedure correctness not reviewed; do not assume this is a correct solution.

The if statement evaluates the temperature condition and executes the code block when true.

*[Knowledge ID: PRC_0330 | Sources: T0036]*

## if statement

### if statement

we have an if statement and this statement has three clauses or three sections here's the first Clause

*[Knowledge ID: DEF_0064 | Sources: T0037]*

### clause

the if Clause, the else if and else clauses are placed after these right braces forming a hierarchy with a parent followed by two children

*[Knowledge ID: DEF_0065 | Sources: T0037]*

braces are only required if we have multiple statements; some people always add braces, others consider them unnecessary noise for single statements

*[Knowledge ID: EXP_0087 | Sources: T0037]*

the else if clause is a little bit indented while the else clause is at the same level as the if clause, which can look ugly; aligning all clauses at the same level improves readability

*[Knowledge ID: EXP_0088 | Sources: T0037]*

braces are only required if we have multiple statements

*[Knowledge ID: FCT_0293 | Sources: T0037]*

## Variable scope in Java code blocks

A variable declared inside a code block is only available within that block; it cannot be accessed outside the block where it was declared.

*[Knowledge ID: EXP_0089 | Sources: T0038]*

Variables can only be declared inside code blocks; declaring a variable outside a block results in a compilation error.

*[Knowledge ID: EXP_0090 | Sources: T0038]*

Assign the boolean variable directly with the expression (income &gt; $100,000); the expression evaluates to true or false, eliminating the need for an explicit if‑else statement.

*[Knowledge ID: EXP_0091 | Sources: T0038]*

If income is greater than $100,000, set hasHighIncome to true; otherwise set it to false.

*[Knowledge ID: FCT_0294 | Sources: T0038]*

Adding curly braces creates a new code block for variable declaration.

*[Knowledge ID: FCT_0295 | Sources: T0038]*

Wrapping a boolean expression in parentheses improves readability but is not required for correctness.

*[Knowledge ID: FCT_0296 | Sources: T0038]*

## ternary operator

### ternary operator

the ternary operator in Java has three pieces: a condition, a value if true, and a value if false; it returns one of the two values based on the condition

*[Knowledge ID: DEF_0066 | Sources: T0039]*

### switch statement

a switch statement executes different parts of code depending on the value of an expression, similar to if statements

*[Knowledge ID: DEF_0067 | Sources: T0039]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
is the income or customers now depending on their income you want to put these customers in different classes if their income is more than $100,000 you want to put them in the first class otherwise we want to put them in the economy class so here's one way to implement the scenario we declare this string variable class name note that we cannot call this class because class is a reserved keyword so class name now we write our first condition if income is greater than $100,000 we said class name
further but the technique you learned there cannot be used here in other words we cannot add income greater than $100,000 here because here we have a boolean expression but on the left side we have declared a string variable so we want to set this to a different string depending on the result of this expression and this is where we use the ternary operator so we start with our condition then we type a question mark if this condition is true we add this value here otherwise we add the other value

*[Knowledge ID: EXM_0129 | Sources: T0039]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
statements to execute different parts of code depending on the value of an expression kind of similar to if statements let me show you so let's say we're gonna write a program and check the role of the current user and then we're gonna print different messages or give them different features depending on their row so let's declare a string variable called role and here we set this to admin now to check the role of the user we can write an if statement like this if role equals admin then perhaps
we want to print you are an admin now you might be wondering why we have this condition here it's obvious that this condition is always true because we have set roll

*[Knowledge ID: EXM_0130 | Sources: T0039]*

The ternary operator can replace an if‑else statement for assigning a value based on a condition.

*[Knowledge ID: FCT_0297 | Sources: T0039]*

A switch statement selects code to execute based on the value of an expression.

*[Knowledge ID: FCT_0298 | Sources: T0039]*

## switch statement versus if statement for role-based messages

A switch statement can be used instead of multiple if/else statements to compare a variable (e.g., role) against constant values (e.g., admin, moderator, guest) and execute the matching case block.

*[Knowledge ID: EXP_0092 | Sources: T0040]*

The break statement exits the switch block after a case has been executed; without it, execution falls through to subsequent case blocks.

*[Knowledge ID: EXP_0093 | Sources: T0040]*

If role equals "admin", the program should print "you are an admin".

*[Knowledge ID: FCT_0299 | Sources: T0040]*

If role equals "moderator", the program should print "you are a moderator".

*[Knowledge ID: FCT_0300 | Sources: T0040]*

If role matches none of the specified cases, the default case prints "you are a guest".

*[Knowledge ID: FCT_0301 | Sources: T0040]*

When the switch variable is a string, cases must use string literals; using an integer variable would require numeric case labels.

*[Knowledge ID: FCT_0302 | Sources: T0040]*

> Procedure correctness not reviewed; do not assume this is a correct solution.

A switch statement evaluates the role variable and executes the matching case block, printing the corresponding message and using break statements to prevent fall‑through.

*[Knowledge ID: PRC_0331 | Sources: T0040]*

## FizzBuzz program logic and common error

When the first condition checks only divisibility by 5, numbers divisible by both 5 and 3 (e.g., 15) satisfy that condition and the subsequent else‑if clauses are skipped, resulting in only "fizz" being printed instead of "fizzbuzz".

*[Knowledge ID: EXP_0094 | Sources: T0041]*

If a number is divisible by 5 (remainder zero when using the modulus operator), the program should print "fizz".

*[Knowledge ID: FCT_0303 | Sources: T0041]*

If a number is divisible by 3 (remainder zero when using the modulus operator), the program should print "buzz".

*[Knowledge ID: FCT_0304 | Sources: T0041]*

If a number is divisible by both 5 and 3, the program should print "fizzbuzz".

*[Knowledge ID: FCT_0305 | Sources: T0041]*

If a number is not divisible by 5 or 3, the program should print the number itself.

*[Knowledge ID: FCT_0306 | Sources: T0041]*

> Instructional role: deliberately incorrect demonstration
> explained by: EXP\_0094
> corrected by: EXM\_0131
> alternative: EXM\_0132
> Claim review: CONTRADICTED — Source explicitly calls the ordering wrong. For 15 the divisible-by-5 branch wins before the combined condition. Retained only as a labeled incorrect demonstration.
> INCORRECT DEMONSTRATION — not instructions to follow.

#### Flowchart: Read integer input and determine FizzBuzz output

```mermaid
flowchart TD
    N0["Import and instantiate a Scanner object to read from the terminal."]
    N1["Prompt the user and read an integer into variable #96;number#96; using #96;scanner.nextInt#40;#41;#96;."]
    N2["Check if #96;number #37; 5 == 0#96;; if true, print #34;fizz#34;."]
    N3["Else if #96;number #37; 3 == 0#96;; if true, print #34;buzz#34;."]
    N4["Else if #96;number #37; 5 == 0 #38;#38; number #37; 3 == 0#96;; if true, print #34;fizzbuzz#34;."]
    N5["Else print the number itself."]
    N0 --> N1
    N1 --> N2
    N2 --> N3
    N3 --> N4
    N4 --> N5
```

*[Knowledge ID: PRC_0332 | Sources: T0041]*

> Instructional role: corrected approach
> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
why this line will not be executed so in situations like this you should have the most specific conditions on the top and the most generic ones on the bottom in this case we want to move this condition to the top so if the number is divisible by 5 &amp; 3 we're gonna print fizzbuzz so this is very specific otherwise if the number is only divisible by 5 we print fizz else if it's divisible by 3 we print buzz and finally if none of his conditions is true then we print the same number now let's run the

*[Knowledge ID: EXM_0131 | Sources: T0042]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
of this second condition here instead we're gonna add a code block over here so if the number is divisible by 5 first we check to see if the number is also divisible by 3 if that's the case we print fizzbuzz otherwise we print just fizz like this okay now we no longer need these two lines because we already implemented this concept here so first we check to see if the number is divisible by five if not we check to see if it's divisible by three and otherwise so here is another way to solve this

*[Knowledge ID: EXM_0132 | Sources: T0042]*

## DRY

### DRY

DRY stands for "don't repeat yourself".

*[Knowledge ID: DEF_0068 | Sources: T0042]*

A solution without repetition may use nested if‑else statements, which can make code harder to read; a flatter structure may repeat some checks but is easier to understand. Choosing between them depends on the balance of readability versus duplication.

*[Knowledge ID: EXP_0095 | Sources: T0042]*

Place the most specific conditions at the top of an if‑else chain and the most generic ones at the bottom.

*[Knowledge ID: FCT_0307 | Sources: T0042]*

Repeated expressions in code violate the DRY principle.

*[Knowledge ID: FCT_0308 | Sources: T0042]*

Nested if‑else statements are considered bad practice because they reduce code readability.

*[Knowledge ID: FCT_0309 | Sources: T0042]*

## Print "Hello World" five times using a for loop

A for loop in Java consists of three parts: an initialization of a counter variable, a boolean condition that determines how many times the loop executes, and an increment operation.

*[Knowledge ID: FCT_0310 | Sources: T0043]*

The loop executes its body while the condition is true; after each iteration the counter is incremented, and when the condition becomes false the loop terminates.

*[Knowledge ID: FCT_0311 | Sources: T0043]*

> Procedure correctness not reviewed; do not assume this is a correct solution.

The loop prints "Hello World" five times on the terminal.

*[Knowledge ID: PRC_0003 | Sources: T0043]*

## for loop

A for loop iterates a known number of times, using an initialization, a loop condition, and an increment/decrement operation.

*[Knowledge ID: CON_0019 | Sources: T0044]*

A while loop repeats as long as a condition remains true, with the loop variable typically updated inside the loop body.

*[Knowledge ID: CON_0002 | Sources: T0044]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
one two three four five in contrast if we initialize I to zero and use the less than operator we will get hello word zero one two three four we can also print these numbers in reverse order so we initialize I to five and execute this loop as long as I is greater than zero but here instead of incrementing I we decrement it now we get hello world five four three two one so this is all about for loops next we're gonna look at while loops in this tutorial we're gonna talk about while loops in Java

*[Knowledge ID: EXM_0133 | Sources: T0044]*

> Literal source code unavailable. Original generated snippet retained in the audit only.

Source explanation:
one two three four five in contrast if we initialize I to zero and use the less than operator we will get hello word zero one two three four we can also print these numbers in reverse order so we initialize I to five and execute this loop as long as I is greater than zero but here instead of incrementing I we decrement it now we get hello world five four three two one so this is all about for loops next we're gonna look at while loops in this tutorial we're gonna talk about while loops in Java

*[Knowledge ID: EXM_0134 | Sources: T0044]*

For loops are preferable when the number of iterations is known ahead of time.

*[Knowledge ID: FCT_0312 | Sources: T0044]*

While loops are better suited for situations where the number of iterations is not known in advance.

*[Knowledge ID: FCT_0313 | Sources: T0044]*

String comparison in Java should use the .equals() method rather than the == operator, because == compares object references.

*[Knowledge ID: FCT_0314 | Sources: T0044]*

## while loop vs do-while loop

A while loop checks its condition before each iteration, so if the condition is false the loop body may never execute. A do-while loop checks its condition after the loop body, guaranteeing that the body executes at least once even if the condition is false.

*[Knowledge ID: EXP_0096 | Sources: T0045]*

To compare the value of two strings you must use the equals() method of the String class; using the == operator compares object references, not content.

*[Knowledge ID: EXP_0097 | Sources: T0045]*

Calling toLowerCase() on the user input converts it to all lowercase, allowing the program to recognize commands like "quit" regardless of the case used by the user.

*[Knowledge ID: EXP_0098 | Sources: T0045]*

Creating a new Scanner object inside a loop for each iteration unnecessarily allocates memory and can lead to resource leaks; it is better to instantiate a single Scanner before the loop and reuse it.

*[Knowledge ID: EXP_0099 | Sources: T0045]*

While loops may never execute if their condition is false at the start.

*[Knowledge ID: FCT_0315 | Sources: T0045]*

Do‑while loops always execute their body at least once.

*[Knowledge ID: FCT_0316 | Sources: T0045]*

Instantiating a Scanner inside a loop creates a new object each iteration, which is unnecessary and bad practice.

*[Knowledge ID: FCT_0317 | Sources: T0045]*

Using equals() with a preceding not operator (!input.equals("quit")) checks that the input is not the string "quit".

*[Knowledge ID: FCT_0318 | Sources: T0045]*

Converting input to lowercase with toLowerCase() enables case‑insensitive command detection.

*[Knowledge ID: FCT_0319 | Sources: T0045]*

> Procedure correctness not reviewed; do not assume this is a correct solution.

A loop that continuously prompts the user, reads input, normalizes case, echoes the input, and terminates when the user enters "quit".

*[Knowledge ID: PRC_0010 | Sources: T0045]*

> Procedure correctness not reviewed; do not assume this is a correct solution.

A do‑while loop that guarantees the body runs at least once before checking the quit condition.

*[Knowledge ID: PRC_0011 | Sources: T0045]*

## break statement

When Java sees the break statement it will ignore everything else after and it will terminate the loop.

*[Knowledge ID: EXP_0100 | Sources: T0046]*

When Java sees the continue statement it moves control to the beginning of the loop, causing the remaining statements in the current iteration to be ignored.

*[Knowledge ID: EXP_0101 | Sources: T0046]*

The break statement terminates a loop.

*[Knowledge ID: FCT_0320 | Sources: T0046]*

The continue statement moves control to the beginning of a loop.

*[Knowledge ID: FCT_0321 | Sources: T0046]*

> Procedure correctness not reviewed; do not assume this is a correct solution.

#### Flowchart: Handling quit input in a loop

```mermaid
flowchart TD
    N0["Read user input inside the loop."]
    N1["If the input equals #34;quit#34;, execute a break statement to exit the loop."]
    N2["Otherwise, print the input."]
    N0 --> N1
    N1 --> N2
```

*[Knowledge ID: PRC_0333 | Sources: T0046]*

> Procedure correctness not reviewed; do not assume this is a correct solution.

#### Flowchart: Skipping echo for "pass" input

```mermaid
flowchart TD
    N0["Read user input."]
    N1["If the input equals #34;pass#34;, execute a continue statement to skip printing and start the next iteration."]
    N2["Otherwise, print the input."]
    N0 --> N1
    N1 --> N2
```

*[Knowledge ID: PRC_0334 | Sources: T0046]*

## for each loop

### for each loop

A loop construct in Java used to iterate over arrays or collections without needing an explicit index or counter.

*[Knowledge ID: DEF_0069 | Sources: T0047]*

The for each loop is always forward only and does not provide access to the index of each item; only the value of each item is available.

*[Knowledge ID: EXP_0102 | Sources: T0047, T0048]*

Using a while true loop without a break statement creates an infinite loop that never terminates, which can be dangerous in terms of memory consumption.

*[Knowledge ID: EXP_0103 | Sources: T0047]*

In a for each loop, the loop variable holds the value of each item in the array during each iteration.

*[Knowledge ID: FCT_0322 | Sources: T0047]*

When validating user input, an infinite loop (while true) can be used to repeatedly ask the same question until a valid value is entered.

*[Knowledge ID: FCT_0323 | Sources: T0048]*

> Procedure correctness not reviewed; do not assume this is a correct solution.

Use an infinite loop to repeatedly ask for input until a valid value is entered, breaking out when the condition is satisfied.

*[Knowledge ID: PRC_0335 | Sources: T0048]*

## Variable scope in loops

Whenever a variable is declared inside a block (such as a while loop), its scope is limited to that block; to use the variable elsewhere, declare it outside the block.

*[Knowledge ID: EXP_0104 | Sources: T0049]*

An infinite loop can be used to repeatedly prompt for input until the entered value satisfies the required range, after which the loop is broken.

*[Knowledge ID: EXP_0105 | Sources: T0049]*

The principal variable is scoped to the block in which it is defined and is not available outside that block, causing a compilation error when referenced elsewhere.

*[Knowledge ID: FCT_0324 | Sources: T0049]*

Declaring monthly interest inside a block leads to a compilation error because the variable is not visible outside that block; moving the declaration to the top resolves the error.

*[Knowledge ID: FCT_0325 | Sources: T0049]*

When user input is outside the allowed range, the program prints an error message prompting the user to enter a value within the specified limits.

*[Knowledge ID: FCT_0326 | Sources: T0049]*

## control flow statements

### control flow statements

control flow statements include conditional statements like if and switch for making decisions in programs, as well as loops for executing code repeatedly such as for loops, while loops, do-while loops, and for-each loops, and also break and continue statements for breaking or jumping to the beginning of a loop.

*[Knowledge ID: DEF_0070 | Sources: T0050]*

### clean code

clean code is code that is easy for humans to read, understand, and maintain, achieved by structuring code into smaller, well‑named chunks and applying techniques that improve its readability and maintainability.

*[Knowledge ID: DEF_0071 | Sources: T0050]*

When the code inside a method becomes too long, it hurts maintainability because readers must scan many statements to understand the logic; breaking the code into smaller, logical chunks makes it easier to read and understand.

*[Knowledge ID: EXP_0106 | Sources: T0050]*

break and continue statements are used for breaking or jumping to the beginning of a loop.

*[Knowledge ID: FCT_0327 | Sources: T0050]*

---

*Render complete: 376 items from 48 sections*

### Additional details: DEF_0062
**Content:**
operators used to compare primitive values such as equality (==), inequality (!=), greater than (&gt;), greater than or equal (&gt;=), less than (&lt;), and less than or equal (&lt;=)
Sources: T0034

### Additional details: DEF_0063
**Content:**
operators such as logical AND (&amp;&amp;), logical OR (||), and logical NOT (!) used for implementing real‑world rules
Sources: T0034

### Additional details: EXP_0002
**Topic:**
Java Virtual Machine (JVM) translates bytecode to native code
Sources: T0007

### Additional details: EXP_0006
**Topic:**
int type stores whole numbers
Sources: T0010

### Additional details: EXP_0008
**Topic:**
initializing variables before use
Sources: T0010

### Additional details: EXP_0009
**Topic:**
variable naming convention
Sources: T0010

### Additional details: EXP_0073
**Topic:**
difference between primitive and reference types
Sources: T0013

### Additional details: EXP_0076
**Topic:**
naming convention for constants
Sources: T0022

### Additional details: EXP_0077
**Topic:**
integer division behavior in Java
Sources: T0022

### Additional details: EXP_0078
**Topic:**
casting to obtain floating‑point results
Sources: T0022

### Additional details: EXP_0010
**Topic:**
prefix vs postfix increment
Sources: T0022

### Additional details: EXP_0080
**Topic:**
Casting a double result of Math.random() directly to int yields zero.
Sources: T0027

### Additional details: EXP_0003
**Topic:**
To obtain an integer between 0 and 100 from Math.random(), the entire expression must be multiplied before casting.
Sources: T0027

### Additional details: EXP_0004
**Topic:**
Formatting numbers as currency or percentages in Java.
Sources: T0027

### Additional details: EXP_0082
**Topic:**
Choosing appropriate data types
Sources: T0032

### Additional details: EXP_0083
**Topic:**
Using meaningful variable names
Sources: T0032

### Additional details: EXP_0005
**Content:**
Logical operators (&amp;&amp;, ||, !) are used to combine or invert boolean expressions to implement complex decision rules.
**Topic:**
logical operators usage
Sources: T0034

### Additional details: EXP_0086
**Content:**
Wrap the first condition in parentheses, then use the AND operator (&amp;&amp;) to combine it with the second condition, e.g., (highIncome || goodCredit) &amp;&amp; !hasCriminalRecord.
**Topic:**
Combining conditions with AND operator
Sources: T0036

### Additional details: EXP_0087
**Topic:**
use of braces in single-statement if
Sources: T0037

### Additional details: EXP_0088
**Topic:**
formatting of if‑else chains
Sources: T0037

### Additional details: EXP_0090
**Topic:**
Declaration location restriction
Sources: T0038

### Additional details: EXP_0091
**Content:**
Assign the boolean variable directly with the expression (income &gt; $100,000); the expression evaluates to true or false, eliminating the need for an explicit if‑else statement.
**Topic:**
Simplifying boolean assignment
Sources: T0038

### Additional details: EXP_0093
**Topic:**
purpose of break statement in a switch block
Sources: T0040

### Additional details: EXP_0095
**Topic:**
Trade‑offs between code repetition and nesting
Sources: T0042

### Additional details: EXP_0098
**Topic:**
Case‑insensitive input handling
Sources: T0045

### Additional details: EXP_0099
**Topic:**
Scanner object usage
Sources: T0045

### Additional details: EXP_0102
**Topic:**
limitations of the for each loop
Sources: T0047, T0048

### Additional details: EXP_0103
**Topic:**
danger of while true without a break
Sources: T0047

### Additional details: EXP_0105
**Topic:**
Input validation with infinite loops
Sources: T0049

### Additional details: EXP_0106
**Topic:**
maintainability of code
Sources: T0050

### Additional details: EXM_0011
**Exemplifies:**
printing a variable
Sources: T0010

### Additional details: EXM_0012
**Exemplifies:**
changing a variable's value
Sources: T0010

### Additional details: EXM_0013
**Exemplifies:**
multiple variable declaration on one line (not recommended)
Sources: T0010

### Additional details: EXM_0014
**Exemplifies:**
copying variable value
Sources: T0010

### Additional details: EXM_0108
**Exemplifies:**
boolean variable assignment
Sources: T0012

### Additional details: EXM_0110
**Exemplifies:**
Using endsWith method to test suffix
Sources: T0016

### Additional details: EXM_0004
**Exemplifies:**
Using length method to get string length
Sources: T0016

### Additional details: EXM_0111
**Exemplifies:**
replace method
Sources: T0017

### Additional details: EXM_0005
**Exemplifies:**
indexOf method
Sources: T0017

### Additional details: EXM_0112
**Exemplifies:**
Including double quotes in a string
Sources: T0018

### Additional details: EXM_0113
**Exemplifies:**
Escaping backslashes in a Windows file path
Sources: T0018

### Additional details: EXM_0114
**Exemplifies:**
Using newline and tab escape sequences
Sources: T0018

### Additional details: EXM_0116
**Exemplifies:**
division of whole numbers
Sources: T0022

### Additional details: EXM_0117
**Exemplifies:**
casting to double for floating‑point division
Sources: T0022

### Additional details: EXM_0118
**Exemplifies:**
increment operator as postfix
Sources: T0022

### Additional details: EXM_0015
**Exemplifies:**
increment operator as prefix
Sources: T0022

### Additional details: EXM_0119
**Exemplifies:**
casting a floating‑point value 1.1 to an int results in 1
Sources: T0025

### Additional details: EXM_0120
**Exemplifies:**
parsing a string "1" to an int using Integer.parseInt
Sources: T0025

### Additional details: EXM_0122
**Exemplifies:**
ceil method
Sources: T0026

### Additional details: EXM_0123
**Exemplifies:**
floor method
Sources: T0026

### Additional details: EXM_0124
**Exemplifies:**
max method with integers
Sources: T0026

### Additional details: EXM_0125
**Exemplifies:**
min method with integers
Sources: T0026

### Additional details: EXM_0007
**Exemplifies:**
random method
Sources: T0026

### Additional details: EXM_0008
**Exemplifies:**
x &lt;= y
Sources: T0034

### Additional details: EXM_0128
**Exemplifies:**
If temperature is greater than 30, print "it's a hot day" and "drink plenty of water".
Sources: T0036

### Additional details: EXM_0129
**Exemplifies:**
ternary operator usage for class assignment based on income
Sources: T0039

### Additional details: EXM_0130
**Exemplifies:**
switch statement checking user role
Sources: T0039

### Additional details: EXM_0131
**Exemplifies:**
ordering of specific to generic conditions in an if‑else chain
Sources: T0042

### Additional details: EXM_0132
**Exemplifies:**
alternative implementation that reduces repetition by nesting conditions
Sources: T0042

### Additional details: EXM_0133
**Exemplifies:**
for loop example
Sources: T0044

### Additional details: EXM_0134
**Exemplifies:**
while loop example
Sources: T0044

### Additional details: FCT_0211
**Content:**
to declare an array of integers you write int\[\] followed by the variable name
Sources: T0019

### Additional details: FCT_0287
**Content:**
The expression X &lt;= Y evaluates to true when X is less than or equal to Y.
Sources: T0034

### Additional details: FCT_0288
**Content:**
The &amp;&amp; operator represents logical AND; the expression is true only if both conditions are true. Java evaluates the expression from left to right and stops evaluating further conditions if the first condition is false (short‑circuit evaluation).
Sources: T0035

### Additional details: FRM_0003
**Variables:**
- P: principal or the amount of loan
- R: monthly interest rate (annual rate divided by 100 then by 12)
- n: number of payments (months)
Sources: T0031

### Additional details: PRC_0006
**Steps:**
- Click on the download link for IntelliJ IDEA Community Edition
- Drag and drop the downloaded application onto the Applications folder
Sources: T0002

### Additional details: PRC_0005
**Content:**
Compiling creates a .class file (bytecode) in the output folder.
**Steps:**
- Open a terminal (or command prompt) in the folder containing the source file.
- Run the Java compiler: `javac Main.java` (case‑sensitive on macOS/Linux).
Sources: T0007

### Additional details: PRC_0328
**Content:**
The JVM loads the bytecode and translates it to native code for execution.
**Steps:**
- In the terminal, execute the JVM with the class name: `java Main`.
Sources: T0007

### Additional details: PRC_0007
**Content:**
Compiled class files are stored in the output directory mirroring the source package structure.
**Steps:**
- In the project panel, open the `out` folder to see the compiled `.class` files under the package hierarchy.
Sources: T0007

### Additional details: PRC_0329
**Content:**
The procedure combines logical operators to enforce loan eligibility criteria.
**Steps:**
- Declare boolean variable hasCriminalRecord and set it to false.
- Wrap the first part of the rule (high income OR good credit) in parentheses.
- Combine the first part with the NOT of hasCriminalRecord using the AND operator (&amp;&amp;).
- If the combined expression evaluates to true, the applicant is eligible for the loan.
Sources: T0036

### Additional details: PRC_0330
**Procedure name:**
Use if statement to display messages based on temperature
**Steps:**
- Declare an integer variable temperature and assign a value (e.g., 32).
- Write an if statement with the condition (temperature &gt; 30).
- Enclose the statements to execute inside curly braces {}.
- Inside the block, print "it's a hot day" and "drink plenty of water".
Sources: T0036

### Additional details: PRC_0331
**Procedure name:**
Implement role-based messaging with a switch statement
**Steps:**
- Write the switch keyword followed by parentheses containing the variable to test (e.g., role).
- Open a block with braces and add case clauses for each role value (admin, moderator, etc.), ending each case label with a colon.
- Inside each case block, add the code to print the appropriate message.
- Add a break statement after each case (except the final default case) to exit the switch.
- Optionally add a default case to handle any unmatched role values.
Sources: T0040

### Additional details: PRC_0332
**Content:**
A simple console program that reads a number and prints "fizz", "buzz", "fizzbuzz", or the number based on divisibility rules.
**Steps:**
- Import and instantiate a Scanner object to read from the terminal.
- Prompt the user and read an integer into variable `number` using `scanner.nextInt()`.
- Check if `number % 5 == 0`; if true, print "fizz".
- Else if `number % 3 == 0`; if true, print "buzz".
- Else if `number % 5 == 0 &amp;&amp; number % 3 == 0`; if true, print "fizzbuzz".
- Else print the number itself.
Sources: T0041

### Additional details: PRC_0003
**Steps:**
- Start with the for keyword and an opening parenthesis.
- Initialize a counter variable, e.g., int i = 0.
- Add a semicolon to terminate the initialization statement.
- Write a boolean condition, e.g., i &lt; 5, that determines how many times the loop runs.
- Add a semicolon to terminate the condition.
- Write the increment expression, e.g., i++.
- Close the parentheses and add the loop body; for a single statement no braces are needed.
- Place the statement to be repeated, e.g., System.out.println("Hello World");
- Optionally, add a space and concatenate the counter variable to the output if desired.
- Close the loop with a closing brace if a block was opened.
Sources: T0043

### Additional details: PRC_0010
**Procedure name:**
Read user input in a loop until "quit" is entered
**Steps:**
- Create a single Scanner object outside the loop (e.g., Scanner scanner = new Scanner(System.in);).
- Enter a while loop with condition !input.equals("quit").
- Inside the loop, read a line with scanner.nextLine(), store it in a variable, and immediately convert it to lowercase using toLowerCase().
- Echo the input back to the user (e.g., System.out.println(input);).
- Loop repeats until the user types "quit" (any case).
Sources: T0045

### Additional details: PRC_0011
**Procedure name:**
Implement the same logic using a do‑while loop
**Steps:**
- Create a Scanner object before the loop.
- Start a do block, read input, convert to lowercase, and echo it.
- Close the do block with while (!input.equals("quit"));
Sources: T0045

### Additional details: PRC_0333
**Content:**
A loop that reads input, breaks on "quit", and prints other inputs.
**Steps:**
- Read user input inside the loop.
- If the input equals "quit", execute a break statement to exit the loop.
- Otherwise, print the input.
Sources: T0046

### Additional details: PRC_0334
**Content:**
A loop that ignores "pass" inputs using continue, while printing other inputs.
**Steps:**
- Read user input.
- If the input equals "pass", execute a continue statement to skip printing and start the next iteration.
- Otherwise, print the input.
Sources: T0046

### Additional details: PRC_0335
**Procedure name:**
Validate user input with an infinite loop
**Steps:**
- Wrap the input prompt inside a while true loop.
- Read the user input.
- If the input is within the valid range, break out of the loop; otherwise, display an error message and repeat.
Sources: T0048
